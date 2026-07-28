import os
import sys

def create_project_structure():
    """
    Creates the required directory structure for the llmXive project.
    This includes data/raw, data/results, code, tests/unit, tests/contract,
    contracts, and the specific project folder.
    """
    base_dir = os.getcwd()
    
    directories = [
        "data/raw",
        "data/results",
        "code",
        "tests/unit",
        "tests/contract",
        "contracts",
        "projects/PROJ-975-llmxive-follow-up-extending-from-chatbot"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = os.path.join(base_dir, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    return created_count

if __name__ == "__main__":
    count = create_project_structure()
    print(f"Setup complete. {count} new directories created.")
