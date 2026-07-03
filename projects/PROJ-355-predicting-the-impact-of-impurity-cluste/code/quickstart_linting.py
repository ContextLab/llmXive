"""
Quickstart script to demonstrate running linting and formatting on the project.
This script is idempotent and safe to run multiple times.
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and report the result."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully.")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"⚠️ {description} found issues (this is expected for new code):")
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)
            
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"❌ {description} timed out.")
        return False
    except Exception as e:
        print(f"❌ {description} failed with error: {e}")
        return False

def main():
    """Main entry point for the quickstart linting script."""
    project_root = Path(__file__).resolve().parent.parent
    print(f"Running linting and formatting checks for project: {project_root}")
    
    # 1. Check if tools are installed
    print("\nChecking tool availability...")
    tools_ok = True
    for tool in ["ruff", "black"]:
        try:
            subprocess.run([tool, "--version"], check=True, capture_output=True)
            print(f"✓ {tool} is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"✗ {tool} is NOT installed. Please run: pip install ruff black")
            tools_ok = False
    
    if not tools_ok:
        print("\n❌ Cannot proceed without ruff and black installed.")
        sys.exit(1)
    
    # 2. Run ruff check
    ruff_check_success = run_command(
        ["ruff", "check", "."],
        "Ruff linting check"
    )
    
    # 3. Run black check (dry run)
    black_check_success = run_command(
        ["black", "--check", "--diff", "."],
        "Black formatting check"
    )
    
    # 4. Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Ruff Check: {'✅ Pass' if ruff_check_success else '⚠️ Issues found'}")
    print(f"Black Check: {'✅ Pass' if black_check_success else '⚠️ Issues found'}")
    
    if not ruff_check_success or not black_check_success:
        print("\nTo fix issues automatically, run:")
        print("  ruff check . --fix")
        print("  black .")
        sys.exit(0) # Exit 0 even if issues found, as this is a check script
    else:
        print("\n✅ All checks passed! Code is clean.")

if __name__ == "__main__":
    main()