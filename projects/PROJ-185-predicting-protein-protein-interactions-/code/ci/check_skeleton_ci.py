import sys
from pathlib import Path
from check_skeleton import missing_directories

def main():
    project_root = Path(__file__).resolve().parent.parent.parent
    missing = missing_directories(project_root)
    if missing:
        print(f"CI FAILURE: Missing skeleton directories: {', '.join(missing)}")
        return 1
    print("CI PASS: All skeleton directories present.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
