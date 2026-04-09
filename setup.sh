#!/bin/bash
# Sentinel-V Quick Setup Script
# This script automates the initial setup of Sentinel-V

set -e

echo "╔════════════════════════════════════════╗"
echo "║  SENTINEL-V SETUP WIZARD               ║"
echo "║  Enterprise Security Suite             ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "✅ Python $PYTHON_VERSION detected"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install requirements
echo "📦 Installing dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies installed"

# Create data directory
if [ ! -d "data" ]; then
    echo "📁 Creating data directory..."
    mkdir -p data
    echo "✅ Data directory created"
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✅ .env file created - EDIT WITH YOUR DISCORD WEBHOOK URL"
else
    echo "✅ .env file already exists"
fi

# Create templates directory
if [ ! -d "templates" ]; then
    echo "📁 Creating templates directory..."
    mkdir -p templates
    echo "✅ Templates directory created"
fi

# Check for nginx and openssh-server
echo ""
echo "🔍 Checking system requirements..."

if command -v nginx &> /dev/null; then
    echo "✅ Nginx detected"
else
    echo "⚠️  Nginx not detected (optional for WAF testing)"
fi

if command -v sshd &> /dev/null; then
    echo "✅ SSH Server detected"
else
    echo "⚠️  SSH Server not detected (optional for SSH monitoring testing)"
fi

if command -v iptables &> /dev/null; then
    echo "✅ iptables detected"
else
    echo "❌ iptables not found - required for IP blocking"
    echo "   Install with: sudo apt-get install iptables"
fi

# Summary
echo ""
echo "╔════════════════════════════════════════╗"
echo "║  SETUP COMPLETE!                       ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "📋 Next steps:"
echo "   1. Edit .env file with Discord webhook URL (optional):"
echo "      nano .env"
echo ""
echo "   2. Start Sentinel-V:"
echo "      source venv/bin/activate"
echo "      python3 main.py"
echo ""
echo "   3. Access the dashboard:"
echo "      http://localhost:5000"
echo ""
echo "📖 For more information, see README.md"
echo ""
echo "🔐 To set up as systemd service:"
echo "   sudo cp sentinel-v.service /etc/systemd/system/"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable --now sentinel-v"
echo ""
