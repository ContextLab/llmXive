"""
Script to create the required code directories for the project.
This implements task T001b: Create code directories `code/`, `code/models/`, and `code/utils/`.
The script is idempotent and can be safely re‑run.
"""

from llmxive_toolkit import paths, get_logger

def main() -> None:
    """
    Create the directories required for the code base.
    Uses the llmxive_toolkit.paths helpers which ensure the directories exist.
    """
    log = get_logger(__name__)

    # Define the directories to create
    dirs = [
        paths.code(),                # <project>/code/
        paths.code("models"),        # <project>/code/models/
        paths.code("utils"),         # <project>/code/utils/
    ]

    for d in dirs:
        # `.mkdir` with `parents=True, exist_ok=True` ensures the directory is created
        # if it does not already exist, and does nothing otherwise.
        d.mkdir(parents=True, exist_ok=True)
        log.info(f"Ensured directory exists: {d}")

    log.info("All required code directories have been created.")

if __name__ == "__main__":
    main()
