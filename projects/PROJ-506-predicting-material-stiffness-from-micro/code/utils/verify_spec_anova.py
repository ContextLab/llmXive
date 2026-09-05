import sys
import re
from pathlib import Path

def verify_anova_mention():
    """
    Verifies that 'spec.md' (FR-007) and 'plan.md' (Methodology) explicitly state
    'One-way ANOVA and Tukey HSD'.
    
    Returns:
        bool: True if both documents contain the required text, False otherwise.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    spec_path = project_root / "specs" / "001-predict-stiffness-cnn" / "spec.md"
    plan_path = project_root / "specs" / "001-predict-stiffness-cnn" / "plan.md"
    
    required_phrase = "One-way ANOVA and Tukey HSD"
    
    # Check spec.md
    spec_found = False
    if spec_path.exists():
        content = spec_path.read_text()
        # Look for FR-007 section context if possible, or just the phrase
        if required_phrase in content:
            spec_found = True
            print(f"✓ Found '{required_phrase}' in spec.md")
        else:
            print(f"✗ Missing '{required_phrase}' in spec.md")
    else:
        print(f"✗ File not found: {spec_path}")
    
    # Check plan.md
    plan_found = False
    if plan_path.exists():
        content = plan_path.read_text()
        # Look for Methodology section context if possible, or just the phrase
        if required_phrase in content:
            plan_found = True
            print(f"✓ Found '{required_phrase}' in plan.md")
        else:
            print(f"✗ Missing '{required_phrase}' in plan.md")
    else:
        print(f"✗ File not found: {plan_path}")
    
    return spec_found and plan_found

def main():
    """Entry point for the verification script."""
    print("Verifying Spec/Plan Alignment for T005v...")
    print(f"Required phrase: 'One-way ANOVA and Tukey HSD'")
    print("-" * 50)
    
    success = verify_anova_mention()
    
    print("-" * 50)
    if success:
        print("STATUS: VERIFIED - Proceed to Phase 1.")
        return 0
    else:
        print("STATUS: FAILED - Required text missing. Halt and report.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
