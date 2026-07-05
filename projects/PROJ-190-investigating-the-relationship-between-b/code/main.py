"""
Main orchestrator for the Brain Network Efficiency pipeline.
Currently a placeholder for Phase 1 setup verification.
"""
import sys
from pathlib import Path

# Add code to path if running as script
code_path = Path(__file__).resolve()
sys.path.insert(0, str(code_path.parent))

def main():
    print("Running Phase 1: Setup Verification...")
    
    # 1. Verify directories
    from setup_directories import create_directories
    created = create_directories()
    if created:
        print(f"Created directories: {[str(p) for p in created]}")
    else:
        print("All required directories already exist.")

    # 2. Verify requirements
    req_file = code_path.parent / "requirements.txt"
    if req_file.exists():
        print(f"Found requirements.txt at {req_file}")
        # Optional: parse and print count
    else:
        print("ERROR: requirements.txt not found.")
        return 1

    # 3. Verify README
    read_me = code_path.parent / "README.md"
    if read_me.exists():
        print(f"Found README.md at {read_me}")
    else:
        print("ERROR: README.md not found.")
        return 1

    print("Phase 1 Setup Verification Complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
