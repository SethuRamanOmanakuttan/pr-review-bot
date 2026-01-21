"""
Single File Reviewer - Reviews one Solidity file at a time
"""
from crewai import Task


def create_single_file_review_task(agent, file_data: dict, analysis_data: dict) -> Task:
    """Create a review task for a single file"""
    
    day = analysis_data['day']
    filename = file_data['filename']
    code = file_data['optimized_code']
    
    description = f"""
    Review this single Solidity file for Day {day}:
    
    File: {filename}
    
    ```solidity
    {code}
    ```
    
    Quick quality check:
    
    CRITICAL ISSUES (score <5):
    - Empty file or only comments
    - Syntax errors (won't compile)
    - Missing pragma statement
    - No contract definition
    - Random/nonsense code
    
    MINOR ISSUES (score 5-6):
    - Has pragma and contract but functions are empty
    - Code compiles but doesn't do much
    - Missing some basic elements
    
    GOOD CODE (score 7+):
    - Has pragma statement
    - Has contract definition
    - Has functions with implementation
    - Code makes sense
    
    Provide:
    - quality_score: 1-10
    - issues: brief list of problems (if any)
    - compiles: true/false
    
    Be BRIEF. Only list actual problems.
    """
    
    return Task(
        description=description,
        agent=agent,
        expected_output="Quality score and brief issue list"
    )
