#!/bin/bash

echo "🤖 PR Review Bot - Installation Script"
echo "======================================"
echo ""

# Check Python version
echo "1. Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "   ✅ $PYTHON_VERSION found"
else
    echo "   ❌ Python 3 not found! Please install Python 3.9+"
    exit 1
fi

# Create virtual environment
echo ""
echo "2. Creating virtual environment..."
if [ -d "venv" ]; then
    echo "   ⚠️  venv already exists, skipping..."
else
    python3 -m venv venv
    echo "   ✅ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "3. Activating virtual environment..."
source venv/bin/activate
echo "   ✅ Virtual environment activated"

# Install dependencies
echo ""
echo "4. Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "   ✅ Dependencies installed"

# Create .env file if it doesn't exist
echo ""
echo "5. Setting up environment file..."
if [ -f ".env" ]; then
    echo "   ⚠️  .env already exists, skipping..."
else
    cp .env.example .env
    echo "   ✅ .env file created from template"
    echo "   ⚠️  Please edit .env and add your API keys!"
fi

# Test setup
echo ""
echo "6. Testing setup..."
python3 test_setup.py

echo ""
echo "======================================"
echo "✨ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your API keys:"
echo "   nano .env"
echo ""
echo "2. Test the setup:"
echo "   python3 test_setup.py"
echo ""
echo "3. Run the bot:"
echo "   python3 main.py --pr <PR_NUMBER> --dry-run"
echo ""
echo "======================================"
