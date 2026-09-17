"""
T062: Verify Methodology & Reporting

Logic:
1. Checks `data-model.md` for explicit contrast with standard OLS.
2. Checks `plan.md` for uncertainty visualization logic.
3. Checks `plan.md` for report disclaimer requirements.

Verification:
- Exits 0 if all required sections and logic descriptions are present.
- Exits 1 if any required section is missing or insufficient.
"""
import sys
from pathlib import Path
import re

def get_project_root() -> Path:
    """Returns the root directory of the project."""
    return Path(__file__).resolve().parent.parent

def read_file(file_path: Path) -> str:
    """Reads a file and returns its contents as a string."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return file_path.read_text(encoding="utf-8")

def check_data_model_ols_contrast(content: str) -> bool:
    """
    Checks if data-model.md contains explicit contrast with standard OLS.
    Looks for keywords like 'robust', 'cluster', 'heteroskedasticity', 'OLS', 'standard errors'.
    """
    # Pattern to detect discussion of OLS limitations or robust alternatives
    # We look for a comparison or explicit mention of why we differ from standard OLS
    patterns = [
        r'robust.*standard.*errors',
        r'cluster.*robust',
        r'heteroskedasticity',
        r'different.*from.*standard.*OLS',
        r'contrast.*with.*OLS',
        r'HC\d',  # Matches HC0, HC1, HC2, HC3
        r'statsmodels.*robust'
    ]
    
    combined_pattern = re.compile('|'.join(patterns), re.IGNORECASE)
    return bool(combined_pattern.search(content))

def check_plan_uncertainty_visualization(content: str) -> bool:
    """
    Checks if plan.md contains uncertainty visualization logic.
    Looks for keywords like 'plot', 'visualize', 'confidence', 'CI', 'sensitivity plot'.
    """
    patterns = [
        r'uncertainty.*visualization',
        r'visualize.*uncertainty',
        r'confidence.*interval.*plot',
        r'sensitivity.*plot',
        r'plot.*coefficient.*stability',
        r'generate.*plot.*sensitivity'
    ]
    
    combined_pattern = re.compile('|'.join(patterns), re.IGNORECASE)
    return bool(combined_pattern.search(content))

def check_plan_disclaimer_requirements(content: str) -> bool:
    """
    Checks if plan.md contains report disclaimer requirements.
    Looks for keywords like 'associational', 'observational', 'disclaimer', 'causal'.
    """
    patterns = [
        r'associational.*nature',
        r'observational.*design',
        r'disclaimer.*causal',
        r'not.*causal.*inference',
        r'limitation.*observational',
        r'associational.*disclaimer'
    ]
    
    combined_pattern = re.compile('|'.join(patterns), re.IGNORECASE)
    return bool(combined_pattern.search(content))

def main() -> int:
    project_root = get_project_root()
    
    data_model_path = project_root / "data-model.md"
    plan_path = project_root / "plan.md"
    
    errors = []
    
    # Check data-model.md
    try:
        data_model_content = read_file(data_model_path)
        if not check_data_model_ols_contrast(data_model_content):
            errors.append("data-model.md: Missing explicit contrast with standard OLS.")
    except FileNotFoundError as e:
        errors.append(str(e))
    
    # Check plan.md
    try:
        plan_content = read_file(plan_path)
        
        if not check_plan_uncertainty_visualization(plan_content):
            errors.append("plan.md: Missing uncertainty visualization logic.")
        
        if not check_plan_disclaimer_requirements(plan_content):
            errors.append("plan.md: Missing report disclaimer requirements.")
            
    except FileNotFoundError as e:
        errors.append(str(e))
    
    if errors:
        print("VERIFICATION FAILED: Methodology & Reporting checks did not pass.")
        for error in errors:
            print(f"  - {error}")
        return 1
    
    print("VERIFICATION PASSED: Methodology & Reporting checks successful.")
    print("  - data-model.md: Contains explicit contrast with standard OLS.")
    print("  - plan.md: Contains uncertainty visualization logic.")
    print("  - plan.md: Contains report disclaimer requirements.")
    return 0

if __name__ == "__main__":
    sys.exit(main())