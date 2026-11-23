"""
Script to run the Budget Compliance Report (T056).

Usage:
python scripts/run_budget_report.py --config data/power_config.yaml --marker results/logs/pipeline_start_time.json --output results/analysis/budget_compliance_report.json
"""
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from utils.budget_report import main

if __name__ == "__main__":
    main()