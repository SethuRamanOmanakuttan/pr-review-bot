"""
Get PR Numbers Script - Fetch PRs from a specific date range
"""
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from github import Github

def get_prs_in_date_range(start_date, end_date):
    """
    Get all PR numbers within a date range
    
    Args:
        start_date: Start date (datetime object)
        end_date: End date (datetime object)
    
    Returns:
        List of PR numbers
    """
    # Load environment variables
    load_dotenv()
    
    token = os.getenv('GITHUB_TOKEN')
    repo_name = os.getenv('GITHUB_REPO')
    
    if not token or not repo_name:
        raise ValueError("GITHUB_TOKEN and GITHUB_REPO must be set in .env file")
    
    # Initialize GitHub client
    print(f"Connecting to GitHub repository: {repo_name}")
    client = Github(token)
    repo = client.get_repo(repo_name)
    
    # Get all PRs (both open and closed)
    print(f"\nFetching PRs from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
    
    prs_in_range = []
    
    # Fetch all PRs (state='all' gets both open and closed)
    pulls = repo.get_pulls(state='all', sort='created', direction='desc')
    
    for pr in pulls:
        # Check if PR was created in the date range
        if start_date <= pr.created_at <= end_date:
            prs_in_range.append({
                'number': pr.number,
                'title': pr.title,
                'author': pr.user.login,
                'created_at': pr.created_at,
                'state': pr.state,
                'merged': pr.merged
            })
            print(f"  Found PR #{pr.number}: {pr.title[:50]}... (by {pr.user.login})")
        
        # Stop if we've gone past the start date
        if pr.created_at < start_date:
            break
    
    return prs_in_range


def main():
    """Main entry point"""
    # Define date range: June 1, 2025 to July 31, 2025 (UTC timezone)
    start_date = datetime(2025, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
    end_date = datetime(2025, 7, 31, 23, 59, 59, tzinfo=timezone.utc)
    
    print("="*60)
    print("PR FETCHER - June-July 2025")
    print("="*60)
    
    try:
        prs = get_prs_in_date_range(start_date, end_date)
        
        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")
        print(f"Total PRs found: {len(prs)}")
        print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # Group by state
        open_prs = [pr for pr in prs if pr['state'] == 'open']
        closed_prs = [pr for pr in prs if pr['state'] == 'closed']
        merged_prs = [pr for pr in prs if pr['merged']]
        
        print(f"\nOpen: {len(open_prs)}")
        print(f"Closed: {len(closed_prs)}")
        print(f"Merged: {len(merged_prs)}")
        
        # Print PR numbers only
        print(f"\n{'='*60}")
        print("PR NUMBERS (for batch review)")
        print(f"{'='*60}")
        pr_numbers = [pr['number'] for pr in prs]
        print(", ".join(map(str, pr_numbers)))
        
        # Save to file
        output_file = "pr_numbers_june_july_2025.txt"
        with open(output_file, 'w') as f:
            f.write(f"# PRs from June-July 2025\n")
            f.write(f"# Total: {len(prs)}\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for pr in prs:
                f.write(f"{pr['number']}\n")
        
        print(f"\n✅ PR numbers saved to: {output_file}")
        
        # Save detailed info
        detailed_file = "pr_details_june_july_2025.txt"
        with open(detailed_file, 'w') as f:
            f.write(f"PRs from June-July 2025\n")
            f.write(f"{'='*80}\n\n")
            
            for pr in prs:
                f.write(f"PR #{pr['number']}: {pr['title']}\n")
                f.write(f"  Author: {pr['author']}\n")
                f.write(f"  Created: {pr['created_at'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"  State: {pr['state']} {'(merged)' if pr['merged'] else ''}\n")
                f.write(f"\n")
        
        print(f"✅ Detailed info saved to: {detailed_file}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
