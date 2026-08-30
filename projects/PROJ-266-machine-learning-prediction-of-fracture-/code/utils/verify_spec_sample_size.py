"""
Verification script for T005e: Verify spec.md states sample-size assumption as '≥ 500 images'.
"""
import sys
from pathlib import Path

def main():
    spec_path = Path(__file__).parent.parent.parent / "spec.md"
    
    if not spec_path.exists():
        print(f"ERROR: {spec_path} not found.", file=sys.stderr)
        sys.exit(1)
    
    content = spec_path.read_text(encoding="utf-8")
    
    # Check for the exact phrase required by the task
    target_phrase = "≥ 500 images"
    
    if target_phrase in content:
        print("Spec sample size assumption verified")
        sys.exit(0)
    else:
        # Fallback to check for similar phrasing if exact match fails (though task requires exact)
        if "500 images" in content and ("≥" in content or "greater than" in content or "at least" in content):
            print("WARNING: Found '500 images' but exact phrase '≥ 500 images' not found. Check formatting.")
            sys.exit(1)
        
        print(f"ERROR: Spec does not contain the required phrase: '{target_phrase}'", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()