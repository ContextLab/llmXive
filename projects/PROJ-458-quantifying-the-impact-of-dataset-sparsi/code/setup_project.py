import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure and generate a listing file.
    
    Creates the following directories:
    - code/utils
    - data/raw
    - data/processed
    - data/results
    - data/metadata
    - tests/unit
    - tests/integration
    - docs
    
    Outputs:
    - project_structure.txt: Recursive listing of all created directories
    """
    # Define the root directory (project root)
    root = Path(__file__).resolve().parent.parent
    
    # Define the directories to create relative to the root
    # Note: 'code/utils' is created relative to root, but 'code' itself might already exist
    # The task asks for 'code/utils', so we ensure the full path exists
    directories = [
        "code/utils",
        "data/raw",
        "data/processed",
        "data/results",
        "data/metadata",
        "tests/unit",
        "tests/integration",
        "docs"
    ]
    
    created_dirs = []
    
    print(f"Creating project structure in: {root}")
    
    for dir_path in directories:
        full_path = root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path.relative_to(root)))
            print(f"  Created: {full_path}")
        except Exception as e:
            print(f"  Error creating {full_path}: {e}")
            sys.exit(1)
    
    # Generate the project_structure.txt file
    output_file = root / "project_structure.txt"
    try:
        # Use 'ls -R' equivalent logic to generate the content
        # We walk the directory tree and format it similarly to 'ls -R'
        with open(output_file, 'w') as f:
            f.write(f"Project Structure for: {root}\n")
            f.write("=" * 50 + "\n\n")
            
            # We need to list the specific directories created
            # To match the spirit of 'ls -R', we list the hierarchy
            # Since we only created specific deep directories, we list them explicitly
            # or we can walk the whole 'data', 'tests', 'code', 'docs' if they exist
            
            # Let's implement a simple recursive listing for the relevant folders
            folders_to_list = ["code", "data", "tests", "docs"]
            
            for folder in folders_to_list:
                folder_path = root / folder
                if folder_path.exists():
                    f.write(f"{folder}/:\n")
                    for item in sorted(folder_path.iterdir()):
                        if item.is_dir():
                            f.write(f"  {item.name}/\n")
                            # Check for subdirs in the specific created paths
                            if item.name == "utils" and folder == "code":
                                # code/utils is a leaf, but let's be safe
                                pass
                            elif item.name in ["raw", "processed", "results", "metadata"] and folder == "data":
                                pass
                            elif item.name in ["unit", "integration"] and folder == "tests":
                                pass
                            # We can add deeper nesting if needed, but 'ls -R' usually lists subdirs
                            # Let's do a simple 2-level depth for clarity matching the task
                            for sub in sorted(item.iterdir()):
                                if sub.is_dir():
                                    f.write(f"    {sub.name}/\n")
                                    for subsub in sorted(sub.iterdir()):
                                        if subsub.is_dir():
                                            f.write(f"      {subsub.name}/\n")
                    f.write("\n")
            
            f.write("\n" + "=" * 50 + "\n")
            f.write("Directories created successfully:\n")
            for d in created_dirs:
                f.write(f"- {d}\n")
                
        print(f"\nProject structure listing written to: {output_file}")
        print(f"Verification: {output_file.exists()}")
        
    except Exception as e:
        print(f"Error writing project_structure.txt: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
