"""Setup script to establish the project skeleton."""
from pathlib import Path
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def main():
    # Define the required directories
    dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "tests/unit",
        "tests/integration",
        "specs/001-llmxive-follow-up-extending-omniretrieva/contracts",
        "logs",
    ]

    for d in dirs:
        p = paths.path(d)
        p.mkdir(parents=True, exist_ok=True)
        # Create a .keep file to ensure directories are non-empty
        (p / ".keep").touch()
        log.info("Created directory: %s", p)

    log.info("Project skeleton established successfully.")

if __name__ == "__main__":
    main()
