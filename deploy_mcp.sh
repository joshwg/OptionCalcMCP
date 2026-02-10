#!/bin/bash

echo "================================================"
echo "  Option Calculator - MCP Server Deployment"
echo "================================================"
echo ""

echo "Step 1: Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    exit 1
fi
python3 --version
echo "✓ Python found"
echo ""

echo "Step 2: Creating virtual environment in mcp-server..."
cd mcp-server
if [ -d "venv" ]; then
    echo "Virtual environment already exists"
else
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi
echo ""

echo "Step 3: Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

echo "Step 4: Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi
echo "✓ Dependencies installed"
echo ""

echo "Step 5: Testing MCP server locally..."
echo "Starting server (press Ctrl+C to stop)..."
python server.py
echo ""

echo "================================================"
echo "  Local Setup Complete!"
echo "================================================"
echo ""
echo "To deploy to Railway:"
echo "1. Create a Railway account at https://railway.app"
echo "2. Install Railway CLI: npm i -g @railway/cli"
echo "3. Run: railway login"
echo "4. Run: railway init"
echo "5. Run: railway up"
echo ""
echo "Or deploy via GitHub:"
echo "1. Push this code to GitHub"
echo "2. Connect your GitHub repo to Railway"
echo "3. Railway will auto-detect and deploy"
echo ""
