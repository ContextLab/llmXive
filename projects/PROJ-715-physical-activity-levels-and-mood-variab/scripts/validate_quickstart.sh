#!/bin/bash
# Validate quickstart.md execution steps
# This script executes the steps in quickstart.md and captures the exit code.
# It generates a validation log file docs/quickstart_validation.log confirming success.

set -e

echo "Starting quickstart validation..."
LOG_FILE="docs/quickstart_validation.log"

# Ensure docs directory exists
mkdir -p docs

# Clear previous log
> "$LOG_FILE"

{
  echo "Quickstart Validation Log"
  echo "========================="
  echo "Timestamp: $(date -Iseconds)"
  echo ""
  
  echo "Step 1: Installing dependencies..."
  cd code
  if pip install -r requirements.txt > ../"$LOG_FILE" 2>&1; then
    echo "✓ Dependencies installed successfully" >> ../"$LOG_FILE"
  else
    echo "✗ Failed to install dependencies" >> ../"$LOG_FILE"
    echo "ERROR: Dependency installation failed. See log for details."
    exit 1
  fi
  
  echo "Step 2: Running main pipeline..."
  if python main.py --input ../data/processed/daily_aggregates.csv >> ../"$LOG_FILE" 2>&1; then
    echo "✓ Main pipeline executed successfully" >> ../"$LOG_FILE"
  else
    echo "✗ Failed to run main pipeline" >> ../"$LOG_FILE"
    echo "ERROR: Main pipeline execution failed. See log for details."
    exit 1
  fi
  
  echo "Step 3: Verifying output files..."
  if [ -f "../data/processed/daily_aggregates.csv" ] && [ -f "../data/processed/model_results.json" ]; then
    echo "✓ Output files generated successfully" >> ../"$LOG_FILE"
  else
    echo "✗ Output files missing" >> ../"$LOG_FILE"
    echo "ERROR: Expected output files were not generated."
    exit 1
  fi
  
  echo ""
  echo "VALIDATION SUCCESSFUL"
  echo "All quickstart steps completed without errors."
  
} | tee "$LOG_FILE"

echo ""
echo "Validation log saved to: $LOG_FILE"
echo "Quickstart validation completed successfully!"
exit 0
