import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Set

def get_project_root() -> Path:
    """Return the project root directory."""
    # Assuming the script is run from the project root or code directory
    # We look for a specific marker or traverse up
    current = Path(__file__).resolve()
    # Traverse up until we find a directory that looks like the root
    # For PROJ-046, we assume the root is the parent of 'code'
    if current.name == 'code':
        return current.parent
    parent = current.parent
    while parent != parent.parent:
        if (parent / 'tasks.md').exists():
            return parent
        parent = parent.parent
    return current.parent

def read_report_content(report_path: Path) -> str:
    """Read the content of the generated report (HTML or PDF text extraction)."""
    if not report_path.exists():
        raise FileNotFoundError(f"Report file not found: {report_path}")
    
    # For HTML reports, read raw text
    if report_path.suffix.lower() == '.html':
        return report_path.read_text(encoding='utf-8')
    
    # For PDF, we would need a library like PyPDF2, but for this validation
    # we assume the primary output is HTML as per T028 description.
    # If PDF is required, this logic would need expansion.
    raise ValueError(f"Unsupported report format: {report_path.suffix}. Expected .html")

def validate_report(report_content: str) -> Tuple[bool, List[str]]:
    """
    Parse report content and verify presence of all required sections.
    
    Required sections (SC-003):
    1. Descriptive Statistics
    2. ANCOVA Results
    3. Effect Sizes (Cohen's d)
    4. Power Analysis (G*Power)
    5. Sensitivity Analysis
    6. Cronbach's Alpha / Reliability Metrics
    7. Data Exclusion Summary
    
    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_missing_sections)
    """
    required_sections = [
        r"Descriptive\s+Statistics",
        r"ANCOVA\s+Results",
        r"Effect\s+Size",
        r"Power\s+Analysis",
        r"Sensitivity\s+Analysis",
        r"Cronbach",
        r"Exclusion"
    ]
    
    missing = []
    content_lower = report_content.lower()
    
    # Normalize whitespace for regex matching
    normalized_content = re.sub(r'\s+', ' ', content_lower)
    
    for pattern in required_sections:
        if not re.search(pattern, normalized_content, re.IGNORECASE):
            missing.append(pattern)
    
    return len(missing) == 0, missing

def main():
    project_root = get_project_root()
    report_path = project_root / "reports" / "chronotype_moral_analysis.html"
    
    if not report_path.exists():
        print(f"ERROR: Report file not found at {report_path}")
        print("Ensure code/04_report.Rmd has been rendered to reports/chronotype_moral_analysis.html")
        sys.exit(1)
    
    try:
        content = read_report_content(report_path)
        is_valid, missing_sections = validate_report(content)
        
        if is_valid:
            print("SUCCESS: Report validation passed. All required sections present.")
            sys.exit(0)
        else:
            print("FAILURE: Report validation failed.")
            print(f"Missing sections: {', '.join(missing_sections)}")
            sys.exit(1)
            
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()