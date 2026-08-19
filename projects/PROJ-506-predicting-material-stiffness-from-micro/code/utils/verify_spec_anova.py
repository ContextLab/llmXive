import sys
from pathlib import Path
import re

def verify_anova_mention(spec_path: str, plan_path: str) -> bool:
    """
    Verify that spec.md FR-007 and plan.md Methodology explicitly state 
    'One-way ANOVA' and 'Tukey HSD'.
    
    Args:
        spec_path: Path to spec.md
        plan_path: Path to plan.md
        
    Returns:
        bool: True if both documents contain the required phrases, False otherwise.
    """
    spec_content = Path(spec_path).read_text()
    plan_content = Path(plan_path).read_text()
    
    # Check for One-way ANOVA in spec.md (looking for FR-007 context)
    anova_spec_found = re.search(r"One-way\s+ANOVA", spec_content, re.IGNORECASE) is not None
    tukey_spec_found = re.search(r"Tukey\s+HSD", spec_content, re.IGNORECASE) is not None
    
    # Check for One-way ANOVA in plan.md (Methodology section)
    anova_plan_found = re.search(r"One-way\s+ANOVA", plan_content, re.IGNORECASE) is not None
    tukey_plan_found = re.search(r"Tukey\s+HSD", plan_content, re.IGNORECASE) is not None
    
    spec_ok = anova_spec_found and tukey_spec_found
    plan_ok = anova_plan_found and tukey_plan_found
    
    if not spec_ok:
        print(f"FAIL: spec.md missing required phrases. ANOVA: {anova_spec_found}, Tukey: {tukey_spec_found}")
    if not plan_ok:
        print(f"FAIL: plan.md missing required phrases. ANOVA: {anova_plan_found}, Tukey: {tukey_plan_found}")
        
    return spec_ok and plan_ok

def main():
    """Main entry point for verification."""
    project_root = Path(__file__).resolve().parent.parent.parent
    spec_path = project_root / "specs" / "001-predict-stiffness-cnn" / "spec.md"
    plan_path = project_root / "specs" / "001-predict-stiffness-cnn" / "plan.md"
    
    if not spec_path.exists():
        print(f"ERROR: spec.md not found at {spec_path}")
        sys.exit(1)
    if not plan_path.exists():
        print(f"ERROR: plan.md not found at {plan_path}")
        sys.exit(1)
        
    success = verify_anova_mention(str(spec_path), str(plan_path))
    
    if success:
        print("SUCCESS: Spec and Plan alignment verified for One-way ANOVA and Tukey HSD.")
        sys.exit(0)
    else:
        print("FAILURE: Alignment verification failed. Check documents.")
        sys.exit(1)

if __name__ == "__main__":
    main()