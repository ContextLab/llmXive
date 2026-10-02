"""
Task T001: Create Project Structure
Creates the directory hierarchy defined in the plan.
"""
import os
from pathlib import Path

def create_directories():
    """Create the required directory structure for the project."""
    base_path = Path(__file__).resolve().parent.parent
    
    # Define directories to create
    directories = [
        base_path / "code" / "data",
        base_path / "code" / "analysis",
        base_path / "code" / "config",
        base_path / "code" / "tests",
        base_path / "data" / "raw",
        base_path / "data" / "results",
        base_path / "specs" / "001-social-support-resilience",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

def verify_structure():
    """Verify the directory structure and write to verification log."""
    base_path = Path(__file__).resolve().parent.parent
    verification_file = base_path / "data" / "results" / "setup_verification.txt"
    
    # Ensure data/results exists before writing
    (base_path / "data" / "results").mkdir(parents=True, exist_ok=True)
    
    lines = []
    lines.append("Project Structure Verification")
    lines.append("=" * 40)
    lines.append("")
    
    # Tree-like output for code/
    lines.append("code/ structure:")
    code_path = base_path / "code"
    if code_path.exists():
        for root, dirs, files in os.walk(code_path):
            level = len(Path(root).relative_to(code_path).parts)
            indent = "  " * level
            lines.append(f"{indent}{Path(root).name}/")
            sub_indent = "  " * (level + 1)
            for f in files:
                lines.append(f"{sub_indent}{f}")
    else:
        lines.append("  code/ directory not found")
    
    lines.append("")
    
    # Tree-like output for data/
    lines.append("data/ structure:")
    data_path = base_path / "data"
    if data_path.exists():
        for root, dirs, files in os.walk(data_path):
            level = len(Path(root).relative_to(data_path).parts)
            indent = "  " * level
            lines.append(f"{indent}{Path(root).name}/")
            sub_indent = "  " * (level + 1)
            for f in files:
                lines.append(f"{sub_indent}{f}")
    else:
        lines.append("  data/ directory not found")
    
    # Write to file
    with open(verification_file, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"Verification written to: {verification_file}")
    return verification_file

def main():
    """Main entry point for T001."""
    print("Starting T001: Create Project Structure")
    create_directories()
    verify_structure()
    print("T001 completed successfully.")

if __name__ == "__main__":
    main()
