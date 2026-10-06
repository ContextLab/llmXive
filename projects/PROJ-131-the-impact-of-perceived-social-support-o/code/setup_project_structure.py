import os
from pathlib import Path

def create_directories():
    """
    Creates the directory hierarchy defined in the plan for PROJ-131.
    Directories created under the project root.
    """
    # Determine project root relative to this script location
    # Script is at code/setup_project_structure.py, so root is parent of parent
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    # Define directories to create
    dirs = [
        project_root / "code" / "data",
        project_root / "code" / "analysis",
        project_root / "code" / "config",
        project_root / "code" / "tests",
        project_root / "data" / "raw",
        project_root / "data" / "results",
        project_root / "data" / "figures",
        project_root / "specs" / "001-social-support-resilience",
        project_root / "code" / "utils",
        project_root / "code" / "logs",
    ]

    created = []
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        created.append(str(d.relative_to(project_root)))
    
    return created

def verify_structure():
    """
    Verifies the directory structure exists and writes a verification log.
    """
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    results_dir = project_root / "data" / "results"
    
    # Ensure results dir exists for the log
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Use subprocess to run 'tree' if available, otherwise list manually
    import subprocess
    import sys

    tree_output = []
    tree_output.append("=== Project Structure Verification ===")
    tree_output.append(f"Project Root: {project_root}")
    tree_output.append("")

    # Try to run tree command
    try:
        # Run tree on code/
        result_code = subprocess.run(['tree', str(project_root / 'code')], capture_output=True, text=True)
        if result_code.returncode == 0:
            tree_output.append("--- code/ ---")
            tree_output.append(result_code.stdout)
        else:
            # Fallback if tree not installed
            tree_output.append("--- code/ (tree not available, listing manually) ---")
            for root, dirs, files in os.walk(project_root / 'code'):
                level = root.replace(str(project_root), '').count(os.sep)
                indent = ' ' * 2 * level
                tree_output.append(f'{indent}{os.path.basename(root)}/')
                subindent = ' ' * 2 * (level + 1)
                for file in files:
                    tree_output.append(f'{subindent}{file}')
            tree_output.append("")

        # Run tree on data/
        result_data = subprocess.run(['tree', str(project_root / 'data')], capture_output=True, text=True)
        if result_data.returncode == 0:
            tree_output.append("--- data/ ---")
            tree_output.append(result_data.stdout)
        else:
            tree_output.append("--- data/ (tree not available, listing manually) ---")
            for root, dirs, files in os.walk(project_root / 'data'):
                level = root.replace(str(project_root), '').count(os.sep)
                indent = ' ' * 2 * level
                tree_output.append(f'{indent}{os.path.basename(root)}/')
                subindent = ' ' * 2 * (level + 1)
                for file in files:
                    tree_output.append(f'{subindent}{file}')
            
    except FileNotFoundError:
        # 'tree' command not found, fallback to manual listing for both
        tree_output.append("--- code/ (tree command not found) ---")
        for root, dirs, files in os.walk(project_root / 'code'):
            level = root.replace(str(project_root), '').count(os.sep)
            indent = ' ' * 2 * level
            tree_output.append(f'{indent}{os.path.basename(root)}/')
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                tree_output.append(f'{subindent}{file}')
        
        tree_output.append("")
        tree_output.append("--- data/ (tree command not found) ---")
        for root, dirs, files in os.walk(project_root / 'data'):
            level = root.replace(str(project_root), '').count(os.sep)
            indent = ' ' * 2 * level
            tree_output.append(f'{indent}{os.path.basename(root)}/')
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                tree_output.append(f'{subindent}{file}')

    # Write verification log
    log_path = results_dir / "setup_verification.txt"
    with open(log_path, 'w') as f:
        f.write('\n'.join(tree_output))
    
    return log_path

def main():
    print("Creating project directory structure...")
    created_dirs = create_directories()
    print(f"Created directories: {created_dirs}")
    
    print("Verifying structure and writing log...")
    log_path = verify_structure()
    print(f"Verification log written to: {log_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
