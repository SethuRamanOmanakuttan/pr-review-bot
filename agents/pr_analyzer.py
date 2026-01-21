"""
PR Analyzer Agent - Extracts and structures PR information
"""
from crewai import Agent, Task
from utils.file_detector import FileDetector
from utils.token_optimizer import TokenOptimizer


def create_pr_analyzer_agent(llm) -> Agent:
    """Create PR Analyzer Agent"""
    return Agent(
        role='PR Analyzer',
        goal='Extract and structure PR information, detect challenge day, and optimize code for token efficiency',
        backstory="""You are an expert at analyzing pull requests for the 30 Days of Solidity challenge.
        You excel at identifying which day's challenge is being submitted using multiple detection methods.
        You also optimize code to reduce token usage while preserving all important information.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def create_pr_analysis_task(agent: Agent, pr_data: dict, challenges_path: str) -> Task:
    """Create PR analysis task"""
    
    # Extract file information
    file_names = [f['filename'].split('/')[-1] for f in pr_data['files']]
    file_paths = [f['path'] for f in pr_data['files']]
    
    # Validate folder structure: just ensure files are NOT directly in submissions/
    # They must be in at least one subfolder: submissions/<anything>/...
    folder_structure_valid = True
    folder_structure_issues = []
    
    for path in file_paths:
        parts = path.split('/')
        # Must have at least: submissions/<subfolder>/<file>
        if len(parts) < 3:
            folder_structure_valid = False
            folder_structure_issues.append(f"- {path}: Files cannot be directly in submissions/. Please create a subfolder: submissions/<your-name>/")
        elif parts[0] != 'submissions':
            folder_structure_valid = False
            folder_structure_issues.append(f"- {path}: Must be inside 'submissions' folder")
    
    # Detect day
    detector = FileDetector(challenges_path)
    day, method, confidence = detector.detect_day(
        pr_data['title'],
        pr_data['description'],
        file_paths,
        file_names
    )
    
    # Get challenge info
    challenge_info = detector.get_challenge_info(day) if day else {}
    
    # Optimize code for each file
    optimizer = TokenOptimizer()
    optimized_files = []
    total_savings = {'original_tokens': 0, 'optimized_tokens': 0, 'tokens_saved': 0}
    
    for file_data in pr_data['files']:
        original_code = file_data['content']
        optimized_code = optimizer.optimize(original_code)
        savings = optimizer.get_savings(original_code, optimized_code)
        
        optimized_files.append({
            'filename': file_data['filename'],
            'original_code': original_code,
            'optimized_code': optimized_code,
            'savings': savings
        })
        
        total_savings['original_tokens'] += savings['original_tokens']
        total_savings['optimized_tokens'] += savings['optimized_tokens']
        total_savings['tokens_saved'] += savings['tokens_saved']
    
    # Calculate percentage saved
    if total_savings['original_tokens'] > 0:
        total_savings['percentage_saved'] = (
            total_savings['tokens_saved'] / total_savings['original_tokens'] * 100
        )
    else:
        total_savings['percentage_saved'] = 0.0
    
    description = f"""
    Analyze this PR submission for the 30 Days of Solidity challenge:
    
    PR #{pr_data['number']}: {pr_data['title']}
    Author: {pr_data['author']}
    
    Detected Day: {day if day else 'Unknown'}
    Detection Method: {method}
    Confidence: {confidence:.2%}
    
    Challenge: {challenge_info.get('contractName', 'Unknown')}
    Concepts: {', '.join(challenge_info.get('conceptsTaught', []))}
    
    Files submitted: {len(pr_data['files'])}
    Token optimization: {total_savings['percentage_saved']:.1f}% reduction
    
    Provide a structured analysis of this PR.
    """
    
    return Task(
        description=description,
        agent=agent,
        expected_output="Structured analysis with day detection, file information, and token optimization stats"
    ), {
        'day': day,
        'detection_method': method,
        'confidence': confidence,
        'challenge_info': challenge_info,
        'optimized_files': optimized_files,
        'token_savings': total_savings,
        'pr_data': pr_data,
        'folder_structure_valid': folder_structure_valid,
        'folder_structure_issues': folder_structure_issues
    }
