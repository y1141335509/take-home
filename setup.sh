#!/bin/bash

# GridCARE ETL Pipeline - Quick Setup Script
# This script automates the setup process for the interviewer

set -e  # Exit on error

echo "=============================================="
echo "GridCARE ETL Pipeline - Quick Setup"
echo "=============================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version | cut -d' ' -f2)
echo "Found Python $python_version"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing Python dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Setup environment file
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  Please edit .env with your PostgreSQL credentials"
    echo "   Default values work with Docker setup:"
    echo "   docker run --name gridcare-postgres \\"
    echo "     -e POSTGRES_DB=gridcare_etl \\"
    echo "     -e POSTGRES_PASSWORD=postgres \\"
    echo "     -p 5432:5432 -d postgres:14"
    echo ""
else
    echo "✓ .env file already exists"
    echo ""
fi

# Check PostgreSQL connection
echo "Checking PostgreSQL connection..."
source .env

if command -v psql &> /dev/null; then
    if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c '\q' 2>/dev/null; then
        echo "✓ Successfully connected to PostgreSQL"
        echo ""
    else
        echo "⚠️  Could not connect to PostgreSQL"
        echo "   Make sure PostgreSQL is running:"
        echo "   - Local: brew services start postgresql"
        echo "   - Docker: docker ps (check gridcare-postgres)"
        echo ""
    fi
else
    echo "⚠️  psql not found. Skipping connection test."
    echo "   Make sure PostgreSQL is running before running main.py"
    echo ""
fi

echo "=============================================="
echo "Setup Complete!"
echo "=============================================="
echo ""
echo "To run the ETL pipeline:"
echo "  1. Ensure PostgreSQL is running"
echo "  2. Run: python main.py"
echo ""
echo "To deactivate virtual environment later:"
echo "  deactivate"
echo ""
