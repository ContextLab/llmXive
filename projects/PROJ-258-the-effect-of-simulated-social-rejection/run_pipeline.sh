#!/bin/bash
# Run the full analysis pipeline

set -e

echo "Starting pipeline..."

echo "Step 1: Data Ingestion"
python code/ingest.py

echo "Step 2: Preprocessing"
python code/preprocess.py

echo "Step 3: Analysis"
python code/analysis.py

echo "Step 4: Reporting"
python code/report.py

echo "Pipeline completed successfully!"
echo "Results saved to:"
echo "  - data/processed/final_results.json"
echo "  - reports/final_report.md"
