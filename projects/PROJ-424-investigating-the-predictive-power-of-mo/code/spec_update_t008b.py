import re
from pathlib import Path
from datetime import datetime

def update_spec_md():
    """
    Updates spec.md to replace SC-005's statistical test requirement.
    
    Replaces: 'bootstrap difference-of-means test (p ≤ 0.05)'
    With: 'descriptive trend analysis'
    
    Reason: N=3 sample size limitations make bootstrapping statistically invalid.
    """
    spec_path = Path("spec.md")
    
    if not spec_path.exists():
        raise FileNotFoundError(f"spec.md not found at {spec_path}")
    
    content = spec_path.read_text()
    
    # Define the replacement pattern
    old_text = "bootstrap difference-of-means test (p ≤ 0.05)"
    new_text = "descriptive trend analysis"
    
    # Check if the old text exists
    if old_text not in content:
        raise ValueError(
            f"Could not find the expected text '{old_text}' in spec.md. "
            "The spec might have already been updated or the text differs."
        )
    
    # Perform the replacement
    new_content = content.replace(old_text, new_text)
    
    # Write back to the file
    spec_path.write_text(new_content)
    
    # Log the change
    timestamp = datetime.now().isoformat()
    print(f"[T008b] Updated SC-005 at {timestamp}:")
    print(f"  Replaced: '{old_text}'")
    print(f"  With:     '{new_text}'")
    print(f"  Reason:   N=3 limitations require trend analysis over hypothesis testing.")
    
    return True

def main():
    try:
        update_spec_md()
        print("T008b spec update completed successfully.")
    except Exception as e:
        print(f"Error updating spec.md: {e}")
        raise

if __name__ == "__main__":
    main()
