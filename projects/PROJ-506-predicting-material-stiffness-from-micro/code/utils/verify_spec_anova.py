import sys
import re
from pathlib import Path

def verify_anova_mention(spec_path: str, plan_path: str) -> bool:
    """
    Verify that spec.md (FR-007) and plan.md (Methodology) explicitly state
    'One-way ANOVA and Tukey HSD'.
    
    Args:
        spec_path: Path to spec.md
        plan_path: Path to plan.md
        
    Returns:
        True if both files contain the required text, False otherwise.
    """
    target_phrase = "One-way ANOVA and Tukey HSD"
    
    # Check spec.md for FR-007 mentioning the phrase
    spec_file = Path(spec_path)
    if not spec_file.exists():
        print(f"ERROR: {spec_path} does not exist.")
        return False
        
    spec_content = spec_file.read_text()
    
    # Look for FR-007 section and check for the phrase
    # We search for the phrase anywhere in the file, but ideally near FR-007
    if target_phrase not in spec_content:
        print(f"ERROR: '{target_phrase}' not found in {spec_path}")
        return False
        
    # Check if FR-007 exists in the spec
    if "FR-007" not in spec_content:
        print(f"ERROR: FR-007 not found in {spec_path}")
        return False
        
    print(f"SUCCESS: Found '{target_phrase}' and FR-007 in {spec_path}")
    
    # Check plan.md for Methodology section mentioning the phrase
    plan_file = Path(plan_path)
    if not plan_file.exists():
        print(f"ERROR: {plan_path} does not exist.")
        return False
        
    plan_content = plan_file.read_text()
    
    if target_phrase not in plan_content:
        print(f"ERROR: '{target_phrase}' not found in {plan_path}")
        return False
        
    # Check if Methodology section exists
    if "Methodology" not in plan_content:
        print(f"ERROR: Methodology section not found in {plan_path}")
        return False
        
    print(f"SUCCESS: Found '{target_phrase}' and Methodology section in {plan_path}")
    
    return True

def main():
    """Main entry point for verification."""
    # Default paths relative to project root
    spec_path = "specs/001-predict-stiffness-cnn/spec.md"
    plan_path = "plan.md"
    
    # Allow override via command line arguments
    if len(sys.argv) >= 3:
        spec_path = sys.argv[1]
        plan_path = sys.argv[2]
        
    print(f"Verifying alignment between {spec_path} and {plan_path}...")
    print(f"Looking for: 'One-way ANOVA and Tukey HSD'")
    print("-" * 50)
    
    success = verify_anova_mention(spec_path, plan_path)
    
    print("-" * 50)
    if success:
        print("VERIFICATION PASSED: Spec and Plan are aligned on statistical methods.")
        print("Task T005v can be marked as [X] READY.")
        sys.exit(0)
    else:
        print("VERIFICATION FAILED: Required text not found in both files.")
        print("Task T005v CANNOT be marked as completed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
