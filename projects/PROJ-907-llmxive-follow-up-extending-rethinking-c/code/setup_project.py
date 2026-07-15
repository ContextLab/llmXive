import os
import sys

def create_directories():
    """
    Creates the project directory structure for PROJ-907-llmxive-follow-up-extending-rethinking-c.
    This function implements T001.
    """
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_root = os.path.join(base_path, "PROJ-907-llmxive-follow-up-extending-rethinking-c")
    code_dir = os.path.join(project_root, "code")

    # Define all required subdirectories relative to code_dir
    subdirs = [
        "src",
        "tests",
        os.path.join("data", "imagenet_trace"),
        os.path.join("data", "imagenet_benchmark"),
        os.path.join("data", "routing_cache"),
        os.path.join("data", "results"),
        "docs"
    ]

    created_paths = []
    for subdir in subdirs:
        full_path = os.path.join(code_dir, subdir)
        try:
            os.makedirs(full_path, exist_ok=True)
            created_paths.append(full_path)
            print(f"Created directory: {full_path}")
        except OSError as e:
            print(f"Error creating directory {full_path}: {e}", file=sys.stderr)
            raise

    if not created_paths:
        print("No directories were created. They may already exist or path construction failed.")
    else:
        print(f"Successfully created {len(created_paths)} directories.")
    
    return created_paths

if __name__ == "__main__":
    create_directories()
