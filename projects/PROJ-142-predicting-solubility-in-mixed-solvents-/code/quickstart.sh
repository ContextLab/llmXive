#!/bin/bash
# Quickstart script for PROJ-142-predicting-solubility-in-mixed-solvents
# This script initializes the project environment and runs the data ingestion pipeline.

set -e

# Define paths relative to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_ROOT/venv"
REQUIREMENTS_FILE="$PROJECT_ROOT/code/requirements.txt"
LOG_FILE="$PROJECT_ROOT/data/artifacts/quickstart_validation.log"

# Ensure data directories exist
mkdir -p "$PROJECT_ROOT/data/raw"
mkdir -p "$PROJECT_ROOT/data/processed"
mkdir -p "$PROJECT_ROOT/data/artifacts"
mkdir -p "$PROJECT_ROOT/code/utils"

echo "=== PROJ-142 Quickstart ===" | tee "$LOG_FILE"
echo "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")" | tee -a "$LOG_FILE"

# Check for virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..." | tee -a "$LOG_FILE"
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Install dependencies if requirements file exists
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Installing dependencies..." | tee -a "$LOG_FILE"
    pip install --quiet --upgrade pip
    pip install --quiet -r "$REQUIREMENTS_FILE"
else
    echo "Warning: requirements.txt not found. Skipping dependency installation." | tee -a "$LOG_FILE"
fi

# Run setup script if exists
if [ -f "$PROJECT_ROOT/code/00_setup_data_dirs.py" ]; then
    echo "Running data directory setup..." | tee -a "$LOG_FILE"
    python "$PROJECT_ROOT/code/00_setup_data_dirs.py" || {
        echo "ERROR: Data directory setup failed." | tee -a "$LOG_FILE"
        exit 1
    }
elif [ -f "$PROJECT_ROOT/code/00_setup_directories.py" ]; then
    echo "Running data directory setup (alternative)..." | tee -a "$LOG_FILE"
    python "$PROJECT_ROOT/code/00_setup_directories.py" || {
        echo "ERROR: Data directory setup failed." | tee -a "$LOG_FILE"
        exit 1
    }
else
    echo "Warning: No setup script found. Skipping directory setup." | tee -a "$LOG_FILE"
fi

# Run data ingestion pipeline if exists
if [ -f "$PROJECT_ROOT/code/01_data_ingestion.py" ]; then
    echo "Running data ingestion pipeline..." | tee -a "$LOG_FILE"
    python "$PROJECT_ROOT/code/01_data_ingestion.py" || {
        echo "ERROR: Data ingestion pipeline failed." | tee -a "$LOG_FILE"
        exit 1
    }
else
    echo "Warning: Data ingestion script not found. Skipping pipeline execution." | tee -a "$LOG_FILE"
fi

# Run feature engineering if exists
if [ -f "$PROJECT_ROOT/code/02_feature_engineering.py" ]; then
    echo "Running feature engineering pipeline..." | tee -a "$LOG_FILE"
    python "$PROJECT_ROOT/code/02_feature_engineering.py" || {
        echo "ERROR: Feature engineering pipeline failed." | tee -a "$LOG_FILE"
        exit 1
    }
else
    echo "Warning: Feature engineering script not found. Skipping pipeline execution." | tee -a "$LOG_FILE"
fi

echo "=== Quickstart Complete ===" | tee -a "$LOG_FILE"
echo "Exit code: 0" | tee -a "$LOG_FILE"
deactivate
exit 0
