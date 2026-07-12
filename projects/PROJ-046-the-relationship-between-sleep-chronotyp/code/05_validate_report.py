import os
import re
import sys
from pathlib import Path

def validate_report(report_path: str) -> bool:
    """
    Parse the generated report (HTML) and verify the presence of all required sections.
    
    Required Sections (based on T027 and T028 requirements):
    1. Descriptive Statistics
    2. Chronotype Classification Results
    3. ANCOVA Results (with Bonferroni correction)
    4. Effect Sizes (Cohen's d)
    5. Reliability Metrics (Cronbach's Alpha)
    6. Sensitivity Analysis (Alpha thresholds)
    7. Data Exclusion Summary
    
    Returns:
        bool: True if all sections are present, False otherwise.
    """
    if not os.path.exists(report_path):
        print(f"Error: Report file not found at {report_path}")
        return False

    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading report file: {e}")
        return False

    # Define regex patterns for required sections (case-insensitive)
    # We look for headers or specific text markers that indicate the section exists.
    required_patterns = [
        r"Descriptive\s+Statistics",
        r"Chronotype\s+Classification",
        r"ANCOVA\s+Results",
        r"Effect\s+Sizes",
        r"Cronbach['\u2019]s\s+Alpha",
        r"Reliability\s+Metrics",
        r"Sensitivity\s+Analysis",
        r"Data\s+Exclusion",
        r"Exclusion\s+Summary"
    ]

    missing_sections = []
    for pattern in required_patterns:
        if not re.search(pattern, content, re.IGNORECASE):
            missing_sections.append(pattern)

    if missing_sections:
        print("Validation FAILED. Missing sections:")
        for s in missing_sections:
            print(f"  - {s}")
        return False

    print("Validation PASSED. All required sections found.")
    return True

def main():
    report_path = "reports/chronotype_moral_analysis.html"
    if len(sys.argv) > 1:
        report_path = sys.argv[1]
    
    success = validate_report(report_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
