"""
Test script to verify setup
"""
import os
from dotenv import load_dotenv

def test_setup():
    """Test if everything is configured correctly"""
    print("🔍 Testing PR Review Bot Setup\n")
    
    # Load environment
    load_dotenv()
    
    # Check environment variables
    print("1. Checking environment variables...")
    github_token = os.getenv('GITHUB_TOKEN')
    google_api_key = os.getenv('GOOGLE_API_KEY')
    github_repo = os.getenv('GITHUB_REPO')
    
    if github_token:
        print(f"   ✅ GITHUB_TOKEN found (length: {len(github_token)})")
    else:
        print("   ❌ GITHUB_TOKEN not found!")
        
    if google_api_key:
        print(f"   ✅ GOOGLE_API_KEY found (length: {len(google_api_key)})")
    else:
        print("   ❌ GOOGLE_API_KEY not found!")
        
    if github_repo:
        print(f"   ✅ GITHUB_REPO: {github_repo}")
    else:
        print("   ❌ GITHUB_REPO not found!")
    
    # Check files
    print("\n2. Checking required files...")
    files = [
        'challenges.json',
        'config.yaml',
        'requirements.txt',
        'main.py'
    ]
    
    for file in files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} not found!")
    
    # Check imports
    print("\n3. Checking Python packages...")
    try:
        import crewai
        print(f"   ✅ crewai (version: {crewai.__version__})")
    except ImportError:
        print("   ❌ crewai not installed!")
    
    try:
        import github
        print("   ✅ PyGithub")
    except ImportError:
        print("   ❌ PyGithub not installed!")
    
    try:
        import google.generativeai
        print("   ✅ google-generativeai")
    except ImportError:
        print("   ❌ google-generativeai not installed!")
    
    try:
        from fuzzywuzzy import fuzz
        print("   ✅ fuzzywuzzy")
    except ImportError:
        print("   ❌ fuzzywuzzy not installed!")
    
    # Test token optimizer
    print("\n4. Testing token optimizer...")
    try:
        from utils.token_optimizer import TokenOptimizer
        
        test_code = """
        // This is a comment
        pragma solidity ^0.8.0;
        
        contract Test {
            uint public value;
        }
        """
        
        optimizer = TokenOptimizer()
        optimized = optimizer.optimize(test_code)
        savings = optimizer.get_savings(test_code, optimized)
        
        print(f"   ✅ Token optimizer working")
        print(f"   📊 Test savings: {savings['percentage_saved']:.1f}%")
    except Exception as e:
        print(f"   ❌ Token optimizer error: {e}")
    
    # Test file detector
    print("\n5. Testing file detector...")
    try:
        from utils.file_detector import FileDetector
        
        detector = FileDetector('challenges.json')
        day, method, conf = detector.detect_day(
            "Day 1 submission",
            "My first contract",
            ["/submissions/day-1/user/"],
            ["ClickCounter.sol"]
        )
        
        print(f"   ✅ File detector working")
        print(f"   📊 Test detection: Day {day} ({method}, {conf:.2%})")
    except Exception as e:
        print(f"   ❌ File detector error: {e}")
    
    print("\n" + "="*50)
    if github_token and google_api_key:
        print("✅ Setup looks good! Ready to run:")
        print("   python3 main.py --pr <PR_NUMBER> --dry-run")
    else:
        print("❌ Setup incomplete. Please:")
        print("   1. Copy .env.example to .env")
        print("   2. Add your API keys to .env")
        print("   3. Run this test again")
    print("="*50)

if __name__ == "__main__":
    test_setup()
