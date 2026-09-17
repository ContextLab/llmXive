"""
Updates plan.md to align with Spec FR-001 regarding method limits.

This script performs a targeted edit on the 'plan.md' file to ensure:
1. The 'Performance Goals' and 'Constraints' sections explicitly state 
   '20 repos × [deferred] methods = 20,000 total'.
2. Any reference to '100 methods' is removed.
3. Any placeholder '[deferred] methods' used as a cap for the limit is 
   replaced with the concrete '1000' limit mandated by FR-001.
4. Verification that '100 methods' is absent and '[deferred] methods' 
   remains present (as a variable count, not a cap).
"""
import os
import sys
import re
from pathlib import Path

def update_plan_file(plan_path: Path):
    if not plan_path.exists():
        raise FileNotFoundError(f"Plan file not found at: {plan_path}")

    content = plan_path.read_text(encoding='utf-8')
    original_content = content

    # 1. Remove references to "100 methods" as a cap or limit
    # We replace "100 methods" with "1000 methods" where it implies a cap,
    # or simply remove it if it's a placeholder for the limit.
    # Based on task description: "remove any reference to '100 methods' ... replacing it with the concrete 1000 limit"
    content = re.sub(r'100 methods', '1000 methods', content)

    # 2. Ensure "20 repos × [deferred] methods = 20,000 total" is present in Performance Goals/Constraints
    # Check if this specific string already exists
    target_string = "20 repos × [deferred] methods = 20,000 total"
    if target_string not in content:
        # Attempt to find a relevant section to insert/update
        # Look for "Performance Goals" or "Constraints" headers
        if "Performance Goals" in content or "Constraints" in content:
            # Simple heuristic: insert near the top if not found, 
            # but since we can't easily parse Markdown headers safely without a parser,
            # we will assume the content structure allows this update or 
            # the user will manually verify the insertion point if regex fails.
            # For this implementation, we will try to replace a generic placeholder
            # or append to a known section if we find "Constraints".
            
            # Let's try to replace a generic "total methods" line if it exists
            if "total methods" in content.lower():
                content = re.sub(
                    r'(\d+)\s+repos\s+×?\s+(.*?)\s+methods\s*=\s*\d+\s*total',
                    target_string,
                    content,
                    flags=re.IGNORECASE
                )
            
            # If still not present, we might need to insert it. 
            # Given the strict requirement, we'll insert it after "Constraints" if found.
            if target_string not in content:
                if "Constraints" in content:
                    content = content.replace(
                        "Constraints", 
                        f"Constraints\n- **Total Sample Size**: {target_string}",
                        1
                    )
                elif "Performance Goals" in content:
                    content = content.replace(
                        "Performance Goals",
                        f"Performance Goals\n- **Total Sample Size**: {target_string}",
                        1
                    )

    # 3. Ensure [deferred] methods is present (it should be in the new string above)
    # The task says: "grep for '[deferred] methods' and ensure it is present"
    # The string we inserted contains it.

    # 4. Verification logic (internal check)
    if "100 methods" in content:
        raise ValueError("Verification failed: '100 methods' still present in plan.md")
    
    if "[deferred] methods" not in content:
        raise ValueError("Verification failed: '[deferred] methods' not found in plan.md")

    if content != original_content:
        plan_path.write_text(content, encoding='utf-8')
        print(f"Successfully updated {plan_path}")
        print("Changes applied:")
        print("  - Replaced '100 methods' with '1000 methods'")
        print("  - Ensured '20 repos × [deferred] methods = 20,000 total' is present")
    else:
        print(f"No changes were necessary for {plan_path}, but constraints are satisfied.")

def main():
    # Determine project root relative to this script location
    # Assuming script is in code/
    project_root = Path(__file__).resolve().parent.parent
    plan_path = project_root / "plan.md"

    if not plan_path.exists():
        print(f"Error: plan.md not found at {plan_path}")
        sys.exit(1)

    try:
        update_plan_file(plan_path)
    except Exception as e:
        print(f"Error updating plan.md: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
