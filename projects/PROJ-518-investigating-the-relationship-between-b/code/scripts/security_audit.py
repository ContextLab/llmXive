"""
Security audit script for PROJ-518.
Runs 'safety check' on requirements.txt and reports vulnerabilities.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_safety_check(requirements_path: str = "requirements.txt") -> int:
    """
    Run safety check on the requirements file.
    Returns 0 if no critical vulnerabilities, 1 otherwise.
    """
    if not os.path.exists(requirements_path):
        print(f"Error: {requirements_path} not found.")
        return 1

    print(f"Running 'safety check' on {requirements_path}...")
    try:
        # Run safety check
        result = subprocess.run(
            ["safety", "check", "-r", requirements_path],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        # Safety returns 1 if vulnerabilities found, 0 if clean
        if result.returncode == 0:
            print("\n✓ No known vulnerabilities found.")
            return 0
        else:
            print("\n⚠ Vulnerabilities found. Please review and update packages.")
            print("Run 'safety check -r requirements.txt --full-report' for details.")
            return 1
            
    except FileNotFoundError:
        print("Error: 'safety' command not found.")
        print("Install it with: pip install safety")
        return 1
    except Exception as e:
        print(f"Error running safety check: {e}")
        return 1

def update_vulnerable_packages(requirements_path: str = "requirements.txt") -> int:
    """
    Attempt to update vulnerable packages.
    This is a manual guidance function - safety doesn't auto-update.
    """
    print("\nTo update vulnerable packages, run:")
    print("  pip install --upgrade <package_name>")
    print("or use:")
    print("  safety fix")
    print("\nThen regenerate requirements.txt with:")
    print("  pip freeze > requirements.txt")
    return 0

def main():
    """Main entry point for security audit."""
    project_root = Path(__file__).parent.parent.parent
    requirements_path = project_root / "requirements.txt"
    
    if not requirements_path.exists():
        print(f"Error: {requirements_path} not found in project root.")
        sys.exit(1)
    
    print(f"Security Audit for {project_root}")
    print("=" * 50)
    
    exit_code = run_safety_check(str(requirements_path))
    
    if exit_code != 0:
        update_vulnerable_packages(str(requirements_path))
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
