import os
import sys

def main():
    """
    Creates and verifies package initialization files and .gitkeep files
    as per task T004.
    """
    # Define the project root relative to where this script is run
    # Assuming script is run from project root or code/
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    files_to_create = [
        os.path.join(project_root, 'code', '__init__.py'),
        os.path.join(project_root, 'tests', '__init__.py'),
        os.path.join(project_root, 'contracts', '.gitkeep'),
        os.path.join(project_root, 'data', '.gitkeep'),
    ]

    base_content = {
        'code/__init__.py': '# Project code initialization\n',
        'tests/__init__.py': '# Tests package initialization\n',
        'contracts/.gitkeep': '# This directory holds schema definitions and contract files.\n# Placeholder to ensure directory persistence in version control.\n',
        'data/.gitkeep': '# This directory holds data artifacts (raw and processed).\n# Placeholder to ensure directory persistence in version control.\n'
    }

    all_ok = True
    for file_path in files_to_create:
        dir_path = os.path.dirname(file_path)
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path)
                print(f"Created directory: {dir_path}")
            except OSError as e:
                print(f"Error creating directory {dir_path}: {e}")
                all_ok = False
                continue

        # Determine content based on filename
        rel_path = os.path.relpath(file_path, project_root)
        content = base_content.get(rel_path, "# Placeholder\n")

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Created/Wrote: {file_path}")
            
            # Verify non-empty
            if os.path.getsize(file_path) > 0:
                print(f"  -> Verified: Non-empty (size: {os.path.getsize(file_path)} bytes)")
            else:
                print(f"  -> ERROR: File is empty!")
                all_ok = False
        except IOError as e:
            print(f"Error writing file {file_path}: {e}")
            all_ok = False

    if all_ok:
        print("\nTask T004: All initialization files created and verified successfully.")
        return 0
    else:
        print("\nTask T004: Failed to create or verify some files.")
        return 1

if __name__ == '__main__':
    sys.exit(main())