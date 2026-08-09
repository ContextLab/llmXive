"""
Helper script to update quickstart.md with the verification command.
This ensures T072 is part of the run-book.
"""
import re
from pathlib import Path

def main():
    quickstart_path = Path(__file__).parent.parent / "quickstart.md"
    if not quickstart_path.exists():
        print(f"quickstart.md not found at {quickstart_path}")
        return 1

    content = quickstart_path.read_text()
    
    # Check if verification command is already present
    if "python scripts/verify_artifacts.py" in content:
        print("Verification command already present in quickstart.md")
        return 0

    # Find the 'Execution' or 'Run' section and append the verification step
    # Pattern to find the end of the execution steps
    pattern = r"(## Execution.*?)(?=## |\Z)"
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        section = match.group(1)
        # Check if we need to add the verification step
        if "verify_artifacts.py" not in section:
            new_step = """
### Step 6: Verify Artifacts (T072)

```bash
python code/scripts/verify_artifacts.py
```

This step verifies that all output files exist and are valid, and updates the state file.
"""
            # Insert before the next section or at the end
            if match.end() < len(content):
                new_content = content[:match.end()] + new_step + content[match.end():]
            else:
                new_content = content + new_step
            
            quickstart_path.write_text(new_content)
            print("Updated quickstart.md with verification step.")
            return 0
    else:
        # Append to end if no specific section found
        content += """
## Verification (T072)

```bash
python code/scripts/verify_artifacts.py
```
"""
        quickstart_path.write_text(content)
        print("Appended verification step to quickstart.md.")
        return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())