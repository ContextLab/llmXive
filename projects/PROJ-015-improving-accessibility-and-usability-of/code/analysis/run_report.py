"""
Main entry point script to generate the T030 summary report.

This script orchestrates the generation of data/processed/report_summary.txt
by calling the ReportGenerator class.
"""
import sys
from pathlib import Path

# Ensure code directory is in path
code_root = Path(__file__).parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from analysis.report_generator import main

if __name__ == "__main__":
    main()
