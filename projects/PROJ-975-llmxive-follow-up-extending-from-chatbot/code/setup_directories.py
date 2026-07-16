import os
import sys

def create_project_structure():
    """
    Creates the directory structure for the llmXive project.
    Directories created:
      - data/raw
      - data/results
      - code
      - tests/unit
      - tests/contract
      - contracts
      - projects/PROJ-975-llmxive-follow-up-extending-from-chatbot
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
    for dir_path in base_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"Project structure setup complete. {created_count} new directories created.")
    return True

if __name__ == "__main__":
    create_project_structure()
