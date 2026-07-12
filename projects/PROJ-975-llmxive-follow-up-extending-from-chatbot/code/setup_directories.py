import os
import sys

def create_project_structure():
    """
    Creates the required directory structure for the llmXive project.
    This function ensures all necessary folders exist, creating them if they don't.
    """
    base_dirs = [
        "data/raw",
        "data/results",
        "code",
        "tests/unit",
        "tests/contract",
        "contracts",
        "projects/PROJ-975-llmxive-follow-up-extending-from-chatbot"
    ]

    created_count = 0
    existing_count = 0

    for dir_path in base_dirs:
        if os.path.exists(dir_path):
            existing_count += 1
        else:
            os.makedirs(dir_path, exist_ok=True)
            created_count += 1

    return {
        "created": created_count,
        "existing": existing_count,
        "total": len(base_dirs)
    }

if __name__ == "__main__":
    result = create_project_structure()
    print(f"Directory structure setup complete.")
    print(f"Created: {result['created']}")
    print(f"Existing: {result['existing']}")
    print(f"Total: {result['total']}")
    sys.exit(0)
