import sys
import re
from pathlib import Path

def verify_anova_mention(spec_path: str, plan_path: str) -> bool:
    """
    Verify that both the spec and plan files contain mentions of 'ANOVA' and 'Tukey'.
    
    Args:
        spec_path: Path to the spec.md file.
        plan_path: Path to the plan.md file.
        
    Returns:
        True if both files contain 'ANOVA' and 'Tukey', False otherwise.
        
    Raises:
        AssertionError: If the alignment check fails.
    """
    try:
        with open(spec_path, 'r') as f:
            spec_content = f.read()
        
        with open(plan_path, 'r') as f:
            plan_content = f.read()
        
        # Check Spec for ANOVA and Tukey
        if 'ANOVA' not in spec_content:
            raise AssertionError("Spec missing 'ANOVA'")
        if 'Tukey' not in spec_content:
            raise AssertionError("Spec missing 'Tukey'")
        
        # Check Plan for ANOVA and Tukey
        if 'ANOVA' not in plan_content:
            raise AssertionError("Plan missing 'ANOVA'")
        if 'Tukey' not in plan_content:
            raise AssertionError("Plan missing 'Tukey'")
        
        return True
        
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Required file not found: {e.filename}")
    except AssertionError as e:
        # Re-raise assertion errors as they are the core logic
        raise

def main():
    """
    Main entry point for the verification script.
    Expects paths to spec.md and plan.md as arguments or uses defaults.
    """
    # Default paths based on project structure
    base_path = Path(__file__).resolve().parent.parent.parent
    spec_path = base_path / "specs" / "001-predict-stiffness-cnn" / "spec.md"
    plan_path = base_path / "plan.md"
    
    # Allow overriding via command line args
    if len(sys.argv) >= 3:
        spec_path = Path(sys.argv[1])
        plan_path = Path(sys.argv[2])
    elif len(sys.argv) == 2:
        spec_path = Path(sys.argv[1])
    
    print(f"Verifying Spec: {spec_path}")
    print(f"Verifying Plan: {plan_path}")
    
    try:
        success = verify_anova_mention(str(spec_path), str(plan_path))
        if success:
            print("SUCCESS: Spec and Plan alignment verified (ANOVA/Tukey present).")
            sys.exit(0)
        else:
            print("FAILURE: Alignment check failed.")
            sys.exit(1)
    except AssertionError as e:
        print(f"VERIFICATION FAILED: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"FILE ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()