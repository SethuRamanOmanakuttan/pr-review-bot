"""
Challenge Validator Agent - Validates against day-specific requirements
"""
from crewai import Agent, Task


def create_challenge_validator_agent(llm) -> Agent:
    """Create Challenge Validator Agent"""
    return Agent(
        role='Challenge Validator',
        goal='Validate that the submission meets the day-specific challenge requirements with flexibility for beginners',
        backstory="""You are an understanding instructor who validates student submissions for the 30 Days of Solidity challenge.
        You check if students have attempted the required concepts, but you're flexible - 50% coverage is enough!
        You focus on whether they tried and understood the core idea, not perfection.
        You celebrate their progress and gently point out what they could explore next.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def create_challenge_validation_task(agent: Agent, analysis_data: dict) -> Task:
    """Create challenge validation task"""
    
    optimized_files = analysis_data['optimized_files']
    challenge_info = analysis_data['challenge_info']
    day = analysis_data['day']
    
    main_file = max(optimized_files, key=lambda x: len(x['optimized_code']))
    
    concepts = challenge_info.get('conceptsTaught', [])
    example_app = challenge_info.get('exampleApplication', '')
    
    description = f"""
    Quick validation for Day {day} beginner submission:
    
    Expected: {', '.join(concepts[:2])}  (just need 1-2 of these)
    
    ```solidity
    {main_file['optimized_code']}
    ```
    
    Check:
    1. Related to Day {day} topic?
    2. Has at least 1 expected concept?
    3. Shows they tried?
    
    Keep it BRIEF. If it's related and shows effort, approve it!
    Only flag if completely wrong challenge or empty.
    
    Format: concepts_found, relevance_score (1-10, be generous)
    """
    
    return Task(
        description=description,
        agent=agent,
        expected_output="Structured validation with concept coverage, functionality check, relevance score, and encouraging feedback"
    )
