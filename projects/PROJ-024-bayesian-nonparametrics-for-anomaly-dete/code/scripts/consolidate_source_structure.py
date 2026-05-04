"""
Consolidate source code to code/src/ subdirectories structure.

This script reorganizes the codebase from flat structure to:
- code/src/models/
- code/src/services/
- code/src/baselines/
- code/src/data/
- code/src/utils/
- code/src/evaluation/

Also updates all import paths across Python files.
"""
import os
import sys
import shutil
from pathlib import Path
import re
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the source file to directory mapping
FILE_MAPPING = {
    # Models
    'models/dp_gmm.py': 'models/dpgmm.py',
    'models/anomaly_score.py': 'models/anomaly_score.py',
    'models/time_series.py': 'models/time_series.py',
    # Services
    'services/threshold_calibrator.py': 'services/threshold_calibrator.py',
    'services/anomaly_detector.py': 'services/anomaly_detector.py',
    # Baselines
    'baselines/arima.py': 'baselines/arima.py',
    'baselines/moving_average.py': 'baselines/moving_average.py',
    'baselines/lstm_ae.py': 'baselines/lstm_ae.py',
    # Data
    'data/synthetic_generator.py': 'data/synthetic_generator.py',
    'data/download_datasets.py': 'data/download_datasets.py',
    # Utils
    'utils/streaming.py': 'utils/streaming.py',
    'utils/checksums.py': 'utils/checksums.py',
    'utils/elbo_logger.py': 'utils/elbo_logger.py',
    # Evaluation
    'evaluation/metrics.py': 'evaluation/metrics.py',
    'evaluation/plots.py': 'evaluation/plots.py',
    'evaluation/statistical_tests.py': 'evaluation/statistical_tests.py',
}

def create_directory_structure(project_root: Path) -> None:
    """Create the src subdirectory structure."""
    src_dirs = [
        project_root / 'code' / 'src' / 'models',
        project_root / 'code' / 'src' / 'services',
        project_root / 'code' / 'src' / 'baselines',
        project_root / 'code' / 'src' / 'data',
        project_root / 'code' / 'src' / 'utils',
        project_root / 'code' / 'src' / 'evaluation',
    ]
    
    for directory in src_dirs:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {directory}")
        
        # Create __init__.py for each package
        init_file = directory / '__init__.py'
        if not init_file.exists():
            init_file.write_text(f'"""{directory.name} package."""\n')
            logger.info(f"Created __init__.py in {directory}")

def get_python_files(directory: Path) -> list:
    """Get all Python files in a directory recursively."""
    python_files = []
    for py_file in directory.rglob('*.py'):
        if py_file.name != '__init__.py':
            python_files.append(py_file)
    return python_files

def update_imports_in_file(file_path: Path, old_to_new_mapping: dict) -> bool:
    """Update import statements in a Python file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        # Update import paths
        for old_pattern, new_pattern in old_to_new_mapping.items():
            # Match import statements like: from src.models.dpgmm import ...
            content = re.sub(
                rf'from\s+{re.escape(old_pattern)}\s+import',
                f'from {new_pattern} import',
                content
            )
            # Match import statements like: import src.models.dpgmm
            content = re.sub(
                rf'import\s+{re.escape(old_pattern)}(\s+as\s+\w+)?',
                f'import {new_pattern}\1',
                content
            )
            # Match relative imports like: from ..models import
            content = re.sub(
                rf'from\s+\.\.(\w+)\.{re.escape(old_pattern.split(".")[-1])}\s+import',
                f'from ..{new_pattern.split(".")[-1]} import',
                content
            )
        
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            logger.info(f"Updated imports in {file_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error updating imports in {file_path}: {e}")
        return False

def move_files(project_root: Path) -> None:
    """Move files to their new locations."""
    src_root = project_root / 'code'
    
    # Create old to new path mapping for import updates
    old_to_new_mapping = {}
    
    for old_relative, new_relative in FILE_MAPPING.items():
        old_path = src_root / old_relative
        if old_path.exists():
            # Determine target directory based on new path
            target_dir = src_root / 'src' / new_relative.split('/')[0]
            target_path = target_dir / new_relative.split('/')[-1]
            
            logger.info(f"Moving {old_path} -> {target_path}")
            
            # Handle file name changes (e.g., dp_gmm.py -> dpgmm.py)
            if old_path.name != target_path.name:
                logger.info(f"  Renaming {old_path.name} -> {target_path.name}")
            
            # Copy file (we'll remove old later after all updates)
            shutil.copy2(old_path, target_path)
            
            # Record mapping for import updates
            old_module = old_relative.replace('/', '.').replace('.py', '')
            new_module = f'src.{new_relative.replace("/", ".")[:-3]}'
            old_to_new_mapping[old_module] = new_module
        else:
            logger.warning(f"File not found (may not exist yet): {old_path}")
    
    return old_to_new_mapping

def update_all_imports(project_root: Path, old_to_new_mapping: dict) -> None:
    """Update imports in all Python files."""
    # Find all Python files to update
    update_dirs = [
        project_root / 'code' / 'scripts',
        project_root / 'code' / 'tests',
        project_root / 'code' / 'src',
    ]
    
    for update_dir in update_dirs:
        if update_dir.exists():
            for py_file in get_python_files(update_dir):
                update_imports_in_file(py_file, old_to_new_mapping)

def create_init_files(project_root: Path) -> None:
    """Create __init__.py files for all packages."""
    src_root = project_root / 'code' / 'src'
    
    # Create __init__.py in src directory
    src_init = src_root / '__init__.py'
    if not src_init.exists():
        src_init.write_text('"""Source package."""\n')
        logger.info("Created __init__.py in code/src/")
    
    # Create __init__.py in each subpackage
    for subdir in ['models', 'services', 'baselines', 'data', 'utils', 'evaluation']:
        init_file = src_root / subdir / '__init__.py'
        if not init_file.exists():
            init_file.write_text(f'"""{subdir} package."""\n')
            logger.info(f"Created __init__.py in code/src/{subdir}/")

def verify_restructure(project_root: Path) -> bool:
    """Verify the restructure was successful."""
    src_root = project_root / 'code' / 'src'
    
    required_dirs = [
        'models',
        'services', 
        'baselines',
        'data',
        'utils',
        'evaluation',
    ]
    
    all_ok = True
    for subdir in required_dirs:
        dir_path = src_root / subdir
        if not dir_path.exists():
            logger.error(f"Missing directory: {dir_path}")
            all_ok = False
        else:
            logger.info(f"Verified directory exists: {dir_path}")
    
    return all_ok

def main():
    """Main entry point for the consolidation script."""
    project_root = Path(__file__).parent.parent.parent
    logger.info(f"Project root: {project_root}")
    
    logger.info("=" * 60)
    logger.info("Starting source code consolidation to code/src/ structure")
    logger.info("=" * 60)
    
    # Step 1: Create directory structure
    logger.info("\n[Step 1] Creating directory structure...")
    create_directory_structure(project_root)
    
    # Step 2: Create __init__.py files
    logger.info("\n[Step 2] Creating __init__.py files...")
    create_init_files(project_root)
    
    # Step 3: Move files
    logger.info("\n[Step 3] Moving files to new locations...")
    old_to_new_mapping = move_files(project_root)
    
    # Step 4: Update imports
    logger.info("\n[Step 4] Updating import statements...")
    if old_to_new_mapping:
        update_all_imports(project_root, old_to_new_mapping)
    else:
        logger.warning("No import updates needed (no files moved)")
    
    # Step 5: Verify
    logger.info("\n[Step 5] Verifying restructure...")
    if verify_restructure(project_root):
        logger.info("=" * 60)
        logger.info("Source code consolidation completed successfully!")
        logger.info("=" * 60)
        return 0
    else:
        logger.error("=" * 60)
        logger.error("Source code consolidation completed with errors!")
        logger.error("=" * 60)
        return 1

if __name__ == '__main__':
    sys.exit(main())
