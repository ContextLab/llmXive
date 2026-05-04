"""
Restructure code files under projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/
to match plan.md specification (move baselines/, models/, evaluation/, utils/ under code/src/)
per Constitution Principle V and filesystem hygiene review.
"""
import os
import sys
import shutil
from pathlib import Path
import re

# Base project path
PROJECT_ROOT = Path(__file__).parent.parent  # code/ directory
SRC_ROOT = PROJECT_ROOT / "src"

# Old locations (current structure based on API surface)
OLD_LOCATIONS = {
    "baselines": PROJECT_ROOT / "baselines",
    "models": PROJECT_ROOT / "models",
    "evaluation": PROJECT_ROOT / "evaluation",
    "data": PROJECT_ROOT / "data",
    "utils": PROJECT_ROOT / "utils",
}

# New locations under src/
NEW_LOCATIONS = {
    "baselines": SRC_ROOT / "baselines",
    "models": SRC_ROOT / "models",
    "evaluation": SRC_ROOT / "evaluation",
    "data": SRC_ROOT / "data",
    "utils": SRC_ROOT / "utils",
}

def create_directory_structure():
    """Create the new src/ directory structure with __init__.py files."""
    print("Creating new directory structure under code/src/...")
    
    for name, path in NEW_LOCATIONS.items():
        path.mkdir(parents=True, exist_ok=True)
        init_file = path / "__init__.py"
        if not init_file.exists():
          init_file.write_text(f'"""{name.capitalize()} module package."""\n')
        print(f"  Created: {path}/")
    
    # Create scripts directory under src/ for utility scripts
    scripts_dir = SRC_ROOT / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    (scripts_dir / "__init__.py").write_text('"""Scripts module package."""\n')
    print(f"  Created: {scripts_dir}/")

def get_python_files(directory):
    """Get all Python files in a directory recursively."""
    if not directory.exists():
        return []
    return list(directory.rglob("*.py"))

def move_files():
    """Move Python files from old locations to new locations."""
    moved_count = 0
    
    for name, old_path in OLD_LOCATIONS.items():
        if not old_path.exists():
            print(f"  Skipping {name}: directory does not exist at {old_path}")
            continue
        
        new_path = NEW_LOCATIONS[name]
        new_path.mkdir(parents=True, exist_ok=True)
        
        for py_file in get_python_files(old_path):
            # Calculate relative path within the old directory
            rel_path = py_file.relative_to(old_path)
            new_file = new_path / rel_path
            
            # Create parent directories if needed
            new_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file (we'll update imports after all moves)
            shutil.copy2(py_file, new_file)
            print(f"  Moved: {py_file.relative_to(PROJECT_ROOT)} -> {new_file.relative_to(PROJECT_ROOT)}")
            moved_count += 1
    
    print(f"\nTotal files moved: {moved_count}")
    return moved_count

def update_imports():
    """Update imports in all moved Python files to use new src/ structure."""
    print("\nUpdating imports in all Python files...")
    updated_count = 0
    
    for name, new_path in NEW_LOCATIONS.items():
        for py_file in get_python_files(new_path):
            content = py_file.read_text()
            original_content = content
            relative_path = py_file.relative_to(SRC_ROOT)
            
            # Pattern to match imports from old locations
            # e.g., from src.models.dpgmm import DPGMMModel
            # e.g., import src.models.dpgmm
            # e.g., from src.evaluation.metrics import EvaluationMetrics
            
            # Update from X import Y patterns
            for old_module in ["baselines", "models", "evaluation", "data", "utils"]:
                if old_module == name:
                    continue  # Skip self-references
                
                # Pattern: from <module>.<submodule> import ...
                pattern_from = rf'from\s+{old_module}\.(\w+)\s+import'
                replacement_from = rf'from src.{old_module}.\1 import'
                content = re.sub(pattern_from, replacement_from, content)
                
                # Pattern: from <module> import ...
                pattern_from_simple = rf'from\s+{old_module}\s+import'
                replacement_from_simple = rf'from src.{old_module} import'
                content = re.sub(pattern_from_simple, replacement_from_simple, content)
                
                # Pattern: import <module>.<submodule>
                pattern_import = rf'import\s+{old_module}\.(\w+)'
                replacement_import = rf'import src.{old_module}.\1'
                content = re.sub(pattern_import, replacement_import, content)
            
            # Handle relative imports within src/
            # e.g., from ..dpgmm import DPGMMModel
            content = re.sub(
                r'from \.\.(\w+)',
                r'from src.\1',
                content
            )
            content = re.sub(
                r'import \.\.(\w+)',
                r'import src.\1',
                content
            )
            
            if content != original_content:
                py_file.write_text(content)
                updated_count += 1
                print(f"  Updated imports: {relative_path}")
    
    print(f"\nTotal files with updated imports: {updated_count}")
    return updated_count

def create_main_entry_points():
    """Create main.py entry points in each module if they don't exist."""
    print("\nCreating main entry points...")
    
    for name, path in NEW_LOCATIONS.items():
        main_file = path / "main.py"
        if not main_file.exists():
            main_content = f'''"""Main entry point for {name} module."""
import sys
from pathlib import Path

def main():
    """Run module-specific main if available."""
    print(f"Running {{name}} module main...")
    # Module-specific logic would be here
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''
            main_file.write_text(main_content)
            print(f"  Created: {main_file.relative_to(PROJECT_ROOT)}")

def verify_restructure():
    """Verify the restructure was successful."""
    print("\nVerifying restructure...")
    issues = []
    
    for name, path in NEW_LOCATIONS.items():
        if not path.exists():
            issues.append(f"Missing directory: {path}")
        else:
            py_files = list(path.rglob("*.py"))
            if py_files:
                print(f"  {name}: {len(py_files)} Python files found")
            else:
                issues.append(f"No Python files in {path}")
    
    if issues:
        print("\nIssues found:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    
    print("  All directories verified successfully!")
    return True

def main():
    """Main restructure function."""
    print("=" * 60)
    print("Code Restructuring Script")
    print("Moving code/ -> code/src/ per plan.md specification")
    print("=" * 60)
    
    # Step 1: Create new directory structure
    create_directory_structure()
    
    # Step 2: Move files
    moved = move_files()
    
    if moved > 0:
        # Step 3: Update imports
        updated = update_imports()
        
        # Step 4: Create entry points
        create_main_entry_points()
    
    # Step 5: Verify
    verify_restructure()
    
    print("\n" + "=" * 60)
    print("Restructure complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run tests to verify imports work correctly")
    print("2. Update any external references to old paths")
    print("3. Delete old directories after verification")
    print("4. Update tasks.md with new file paths")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
    execute: true
    timeout_s: 300