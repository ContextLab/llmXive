import os
import sys
from pathlib import Path
from datetime import datetime

def create_directory_structure():
    """
    Create the project directory structure as defined in T001.
    Returns a list of created paths.
    """
    base = Path(".")
    dirs = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "artifacts/models",
        "artifacts/plots",
        "artifacts/reports",
        "logs"
    ]

    created = []
    for d in dirs:
        p = base / d
        p.mkdir(parents=True, exist_ok=True)
        created.append(str(p))
    
    return created

def write_setup_log(created_dirs):
    """
    Write a success confirmation message with timestamp to logs/setup.log.
    """
    log_path = Path("logs/setup.log")
    timestamp = datetime.now().isoformat()
    
    lines = [
        f"[{timestamp}] Project structure initialization successful.",
        f"Directories created: {len(created_dirs)}",
        "List of directories:",
    ]
    lines.extend([f"  - {d}" for d in sorted(created_dirs)])
    lines.append("")
    lines.append(f"[{timestamp}] Setup complete.")

    with open(log_path, "w") as f:
        f.write("\n".join(lines))

    return log_path

def main():
    """
    Main entry point for T001: Create project structure.
    """
    print("Starting T001: Create project structure...")
    
    # Create directories
    created_dirs = create_directory_structure()
    print(f"Created {len(created_dirs)} directories.")
    
    # Write log
    log_path = write_setup_log(created_dirs)
    print(f"Setup log written to: {log_path}")
    
    # Verification
    if log_path.exists():
        print("Verification: logs/setup.log exists.")
        with open(log_path, "r") as f:
            content = f.read()
            if "successful" in content:
                print("Verification: Log contains success message.")
    else:
        raise RuntimeError("Verification failed: logs/setup.log was not created.")
    
    print("T001 completed successfully.")

if __name__ == "__main__":
    main()
