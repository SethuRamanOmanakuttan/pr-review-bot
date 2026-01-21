"""
PR Review Bot - Main Application
Automated PR review for 30 Days of Solidity submissions
"""
import os
import sys
import yaml
import argparse
import time
from dotenv import load_dotenv
from crewai import Crew, LLM
import google.generativeai as genai

from utils.github_client import GitHubClient
from agents.pr_analyzer import create_pr_analyzer_agent, create_pr_analysis_task
from agents.code_reviewer import create_code_reviewer_agent
from agents.challenge_validator import create_challenge_validator_agent, create_challenge_validation_task
from agents.single_file_reviewer import create_single_file_review_task


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def setup_llm(config: dict):
    """Setup Google Gemini LLM"""
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")
    
    # Configure Gemini
    genai.configure(api_key=api_key)
    
    # Use CrewAI's LLM class with LiteLLM format
    # For Gemini, the format is: gemini/model-name
    model_name = config['llm']['model']
    if not model_name.startswith('gemini/'):
        model_name = f"gemini/{model_name}"
    
    # Create LLM instance for CrewAI
    llm = LLM(
        model=model_name,
        temperature=config['llm']['temperature'],
        api_key=api_key
    )
    
    return llm


def review_pr(pr_number: int, config: dict, dry_run: bool = False, file_delay: int = 5):
    """
    Review a single PR - reviews each file individually
    
    Args:
        pr_number: PR number to review
        config: Configuration dictionary
        dry_run: If True, don't post to GitHub
        file_delay: Delay in seconds between reviewing files (default: 5)
    """
    print(f"\n{'='*60}")
    print(f"REVIEWING PR #{pr_number}")
    print(f"{'='*60}\n")
    
    # Initialize GitHub client
    github_client = GitHubClient(
        os.getenv('GITHUB_TOKEN'),
        os.getenv('GITHUB_REPO')
    )
    
    # Setup LLM
    llm = setup_llm(config)
    
    # Get PR data
    print("📥 Fetching PR data...")
    pr_data = github_client.get_pr(pr_number)
    
    print(f"✅ PR fetched: {pr_data['title']}")
    print(f"   Author: {pr_data['author']}")
    print(f"   Files: {len(pr_data['files'])} Solidity file(s)")
    
    if not pr_data['files']:
        print("⚠️  No Solidity files found in this PR")
        return
    
    # Create agents
    print("\n🤖 Initializing AI agents...")
    pr_analyzer = create_pr_analyzer_agent(llm)
    code_reviewer = create_code_reviewer_agent(llm)
    challenge_validator = create_challenge_validator_agent(llm)
    
    # Analyze PR
    print("\n🔍 Analyzing PR structure...")
    analysis_task, analysis_data = create_pr_analysis_task(
        pr_analyzer, pr_data, config['challenges']['path']
    )
    
    analysis_crew = Crew(
        agents=[pr_analyzer],
        tasks=[analysis_task],
        verbose=True
    )
    
    analysis_crew.kickoff()
    
    print(f"\n✅ Detected: Day {analysis_data['day']}")
    print(f"   Challenge: {analysis_data['challenge_info'].get('contractName', 'Unknown')}")
    print(f"   Token savings: {analysis_data['token_savings']['percentage_saved']:.1f}%")
    
    # Check folder structure first
    if not analysis_data.get('folder_structure_valid', True):
        print("\n❌ Folder structure is invalid!")
        folder_issues = analysis_data.get('folder_structure_issues', [])
        for issue in folder_issues:
            print(f"   {issue}")
        
        # Post folder structure feedback and reject
        folder_feedback = "Quick heads up - your files need to be in a subfolder within submissions/, not directly in it.\n\n"
        folder_feedback += "\n".join(folder_issues)
        
        if not dry_run:
            github_client.post_review(pr_number, folder_feedback, event="REQUEST_CHANGES")
            github_client.add_labels(pr_number, [f"day-{analysis_data['day']}", "needs-fix"])
            print("✅ Folder structure feedback posted")
        else:
            print("🔍 DRY RUN - Would post folder structure feedback")
        return
    
    # Review each file individually
    print(f"\n🔍 Reviewing {len(analysis_data['optimized_files'])} files individually...")
    
    file_issues = []  # Track issues per file
    critical_issues_found = False
    
    for i, file_data in enumerate(analysis_data['optimized_files'], 1):
        print(f"\n📄 Reviewing file {i}/{len(analysis_data['optimized_files'])}: {file_data['filename']}")
        
        # Create single-file review task
        file_review_task = create_single_file_review_task(
            code_reviewer, file_data, analysis_data
        )
        
        file_review_crew = Crew(
            agents=[code_reviewer],
            tasks=[file_review_task],
            verbose=False
        )
        
        file_review_result = file_review_crew.kickoff()
        review_text = str(file_review_result)
        
        # Parse review result for quality score and issues
        # Simple parsing - look for quality score and issues
        if "quality_score" in review_text.lower():
            # Extract score (rough parsing)
            import re
            score_match = re.search(r'quality[_\s]*score[:\s]*(\d+)', review_text.lower())
            if score_match:
                quality_score = int(score_match.group(1))
                print(f"   Quality score: {quality_score}/10")
                
                if quality_score < 5:
                    critical_issues_found = True
                    file_issues.append({
                        'filename': file_data['filename'],
                        'score': quality_score,
                        'issues': review_text,
                        'severity': 'critical'
                    })
                    print(f"   ❌ Critical issues found")
                elif quality_score < 7:
                    file_issues.append({
                        'filename': file_data['filename'],
                        'score': quality_score,
                        'issues': review_text,
                        'severity': 'minor'
                    })
                    print(f"   ⚠️  Minor issues found")
                else:
                    print(f"   ✅ Looks good")
        
        # Wait between file reviews to avoid rate limits
        if i < len(analysis_data['optimized_files']):
            print(f"   ⏳ Waiting {file_delay} seconds...")
            time.sleep(file_delay)
    
    # Validate challenge (quick check)
    print("\n🎯 Validating challenge requirements...")
    validation_task = create_challenge_validation_task(challenge_validator, analysis_data)
    validation_crew = Crew(
        agents=[challenge_validator],
        tasks=[validation_task],
        verbose=False
    )
    validation_result = validation_crew.kickoff()
    validation_text = str(validation_result)
    
    # Make final decision based on file reviews
    print("\n⚖️  Making final decision...")
    
    decision_action = "APPROVE"
    feedback_text = ""
    
    if critical_issues_found:
        decision_action = "REJECT"
        print("   ❌ REJECT - Critical issues found in one or more files")
        
        # Build feedback listing problematic files
        feedback_text = "This needs some work:\n\n"
        for issue in file_issues:
            if issue['severity'] == 'critical':
                # Extract brief issue description from review
                feedback_text += f"- {issue['filename']}: Critical quality issues (score: {issue['score']}/10)\n"
        feedback_text += "\nTake another look at the challenge requirements."
        
    elif len(file_issues) > 0:
        decision_action = "REQUEST_CHANGES"
        print("   ⚠️  REQUEST_CHANGES - Minor issues found")
        
        # Build feedback listing files with minor issues
        feedback_text = "Hey, good start! Just need to fix a couple things:\n\n"
        for issue in file_issues:
            feedback_text += f"- {issue['filename']}: Needs improvement (score: {issue['score']}/10)\n"
        feedback_text += "\nUpdate these and we're good."
        
    else:
        decision_action = "APPROVE"
        print("   ✅ APPROVE - All files look good!")
        feedback_text = "Good job! Your code looks solid."
    
    # Prepare labels
    labels = [f"day-{analysis_data['day']}"]
    if decision_action == "APPROVE":
        labels.append("approved")
    elif decision_action == "REQUEST_CHANGES":
        labels.append("needs-fix")
    elif decision_action == "REJECT":
        labels.append("rejected")
    
    # Display results
    print(f"\n{'='*60}")
    print("📊 REVIEW RESULTS")
    print(f"{'='*60}")
    print(f"\n{feedback_text}\n")
    print(f"{'='*60}")
    print(f"Decision: {decision_action}")
    print(f"Labels: {', '.join(labels)}")
    print(f"{'='*60}\n")
    
    # Post to GitHub
    if not dry_run:
        print("📤 Posting review to GitHub...")
        try:
            # Map decision to GitHub review event
            event_map = {
                "APPROVE": "APPROVE",
                "REQUEST_CHANGES": "REQUEST_CHANGES",
                "REJECT": "COMMENT"
            }
            
            github_client.post_review(
                pr_number,
                feedback_text,
                event=event_map[decision_action]
            )
            
            github_client.add_labels(pr_number, labels)
            
            print("✅ Review posted successfully!")
            
            # Auto-merge if approved
            if decision_action == "APPROVE":
                print("\n🔀 Auto-merging PR...")
                merged = github_client.merge_pr(pr_number, merge_method="squash")
                if merged:
                    print("✅ PR merged successfully!")
                else:
                    print("⚠️  Could not auto-merge (may need manual intervention)")
        except Exception as e:
            print(f"❌ Error posting review: {e}")
    else:
        print("🔍 DRY RUN - Review not posted to GitHub")
    
    # Summary
    print(f"\n{'='*60}")
    print("✨ REVIEW COMPLETE")
    print(f"{'='*60}")
    print(f"PR #{pr_number}: {decision_action}")
    print(f"Token savings: {analysis_data['token_savings']['tokens_saved']} tokens")
    print(f"Percentage saved: {analysis_data['token_savings']['percentage_saved']:.1f}%")
    print(f"{'='*60}\n")


def extract_pr_number(pr_input: str) -> int:
    """Extract PR number from URL or direct number"""
    import re
    
    # Check if it's a URL
    if 'github.com' in pr_input or 'pull/' in pr_input:
        # Extract number from URL
        match = re.search(r'/pull/(\d+)', pr_input)
        if match:
            return int(match.group(1))
        else:
            raise ValueError(f"Could not extract PR number from: {pr_input}")
    else:
        # Direct number
        return int(pr_input)


def review_multiple_prs(pr_numbers: list, config: dict, dry_run: bool = False):
    """
    Review multiple PRs in batch with delays
    
    Args:
        pr_numbers: List of PR numbers to review
        config: Configuration dictionary
        dry_run: If True, don't post to GitHub
    """
    pr_delay = config.get('delays', {}).get('between_prs', 15)
    file_delay = config.get('delays', {}).get('between_files', 5)
    
    total_prs = len(pr_numbers)
    print(f"\n{'='*60}")
    print(f"BATCH REVIEW: {total_prs} PR(s)")
    print(f"{'='*60}")
    print(f"Delay between PRs: {pr_delay} seconds")
    print(f"Delay between files: {file_delay} seconds")
    print(f"{'='*60}\n")
    
    results = []
    
    for idx, pr_number in enumerate(pr_numbers, 1):
        print(f"\n{'#'*60}")
        print(f"BATCH PROGRESS: PR {idx}/{total_prs}")
        print(f"{'#'*60}\n")
        
        try:
            review_pr(pr_number, config, dry_run=dry_run, file_delay=file_delay)
            results.append({'pr': pr_number, 'status': 'success'})
        except Exception as e:
            print(f"\n❌ Error reviewing PR #{pr_number}: {e}")
            import traceback
            traceback.print_exc()
            results.append({'pr': pr_number, 'status': 'failed', 'error': str(e)})
        
        # Wait between PRs (except after the last one)
        if idx < total_prs:
            print(f"\n⏳ Waiting {pr_delay} seconds before next PR...\n")
            time.sleep(pr_delay)
    
    # Print summary
    print(f"\n{'='*60}")
    print("BATCH REVIEW SUMMARY")
    print(f"{'='*60}")
    print(f"Total PRs: {total_prs}")
    print(f"Successful: {sum(1 for r in results if r['status'] == 'success')}")
    print(f"Failed: {sum(1 for r in results if r['status'] == 'failed')}")
    print(f"{'='*60}\n")
    
    # Print details
    for result in results:
        status_icon = "✅" if result['status'] == 'success' else "❌"
        print(f"{status_icon} PR #{result['pr']}: {result['status'].upper()}")
        if 'error' in result:
            print(f"   Error: {result['error']}")
    print()


def main():
    """Main entry point"""
    # Load environment variables
    load_dotenv()
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='PR Review Bot for 30 Days of Solidity')
    parser.add_argument('--pr', type=str, nargs='+', required=True, 
                       help='PR number(s) or URL(s) - space separated for multiple (e.g., 123 124 125 or https://github.com/owner/repo/pull/123 124)')
    parser.add_argument('--dry-run', action='store_true', help='Run without posting to GitHub')
    parser.add_argument('--config', default='config.yaml', help='Path to config file')
    
    args = parser.parse_args()
    
    # Extract PR numbers
    pr_numbers = []
    for pr_input in args.pr:
        try:
            pr_number = extract_pr_number(pr_input)
            pr_numbers.append(pr_number)
        except ValueError as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
    
    # Load config
    config = load_config(args.config)
    
    # Review PRs
    try:
        if len(pr_numbers) == 1:
            # Single PR review
            file_delay = config.get('delays', {}).get('between_files', 5)
            review_pr(pr_numbers[0], config, dry_run=args.dry_run, file_delay=file_delay)
        else:
            # Batch review
            review_multiple_prs(pr_numbers, config, dry_run=args.dry_run)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
