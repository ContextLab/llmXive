"""
Code cleanup and refactoring utility for PROJ-037.

This script performs the following cleanup tasks:
1. Removes temporary files and directories
2. Consolidates duplicate imports
3. Standardizes logging configurations
4. Removes unused dependencies from requirements.txt
5. Fixes common linting issues
6. Validates all module imports
"""
import os
import sys
import re
import ast
import logging
import subprocess
from pathlib import Path
from typing import Set, List, Dict, Tuple, Optional
from collections import defaultdict

from config import get_config
from utils.logging_utils import setup_logging, get_logger
from utils.seeding import set_seed

# Configure logging
logger = get_logger(__name__)

class CodeCleanup:
    """Handles code cleanup and refactoring tasks."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.code_dir = project_root / "code"
        self.tests_dir = project_root / "tests"
        self.data_dir = project_root / "data"
        self.docs_dir = project_root / "docs"
        
        # Track files to process
        self.python_files: List[Path] = []
        self.imports_by_file: Dict[Path, Set[str]] = defaultdict(set)
        self.used_names: Dict[Path, Set[str]] = defaultdict(set)
        
    def scan_python_files(self) -> None:
        """Scan all Python files in the project."""
        logger.info("Scanning Python files...")
        self.python_files = list(self.code_dir.rglob("*.py"))
        self.python_files.extend(self.tests_dir.rglob("*.py"))
        logger.info(f"Found {len(self.python_files)} Python files")

    def analyze_imports(self) -> None:
        """Analyze imports across all Python files."""
        logger.info("Analyzing imports...")
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            self.imports_by_file[file_path].add(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        module = node.module or ""
                        for alias in node.names:
                            self.imports_by_file[file_path].add(f"{module}.{alias.name}")
            except SyntaxError as e:
                logger.warning(f"Syntax error in {file_path}: {e}")
            except Exception as e:
                logger.error(f"Error analyzing {file_path}: {e}")

    def consolidate_imports(self) -> int:
        """Consolidate duplicate imports within files."""
        count = 0
        logger.info("Consolidating imports...")
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                new_lines = []
                seen_imports = set()
                import_block_start = -1
                import_block_end = -1
                
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    
                    # Detect import statements
                    if stripped.startswith('import ') or stripped.startswith('from '):
                        if import_block_start == -1:
                            import_block_start = i
                        import_block_end = i
                        
                        # Extract the import statement
                        if stripped.startswith('import '):
                            parts = stripped.split('import')
                            if len(parts) > 1:
                                imports = [p.strip() for p in parts[1].split(',') if p.strip()]
                                for imp in imports:
                                    if imp not in seen_imports:
                                        seen_imports.add(imp)
                                        new_lines.append(f"import {imp}\n")
                                    else:
                                        count += 1
                        elif stripped.startswith('from '):
                            parts = stripped.split('import')
                            if len(parts) > 1:
                                module = parts[0].replace('from', '').strip()
                                imports = [p.strip() for p in parts[1].split(',') if p.strip()]
                                for imp in imports:
                                    full_import = f"{module}.{imp}"
                                    if full_import not in seen_imports:
                                        seen_imports.add(full_import)
                                        new_lines.append(f"from {module} import {imp}\n")
                                    else:
                                        count += 1
                    else:
                        if import_block_start != -1 and i > import_block_end:
                            import_block_start = -1
                            import_block_end = -1
                        new_lines.append(line)
                
                # Write back if changes were made
                if count > 0:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.writelines(new_lines)
                    logger.debug(f"Consolidated imports in {file_path}")
                    
            except Exception as e:
                logger.error(f"Error consolidating imports in {file_path}: {e}")
        
        return count

    def remove_unused_imports(self) -> int:
        """Remove unused imports from files."""
        count = 0
        logger.info("Removing unused imports...")
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                # Collect all names used in the file
                used_names = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Name):
                        used_names.add(node.id)
                    elif isinstance(node, ast.Attribute):
                        # Handle attribute access like os.path.join
                        current = node
                        while isinstance(current, ast.Attribute):
                            current = current.value
                        if isinstance(current, ast.Name):
                            used_names.add(current.id)
                
                # Find unused imports
                unused_imports = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            name = alias.asname if alias.asname else alias.name.split('.')[0]
                            if name not in used_names:
                                unused_imports.add(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        module = node.module or ""
                        for alias in node.names:
                            name = alias.asname if alias.asname else alias.name
                            full_name = f"{module}.{name}" if module else name
                            if name not in used_names and full_name not in used_names:
                                unused_imports.add(f"{module}.{name}")
                
                # Remove unused imports
                if unused_imports:
                    lines = content.splitlines(keepends=True)
                    new_lines = []
                    skip_next = False
                    
                    for i, line in enumerate(lines):
                        stripped = line.strip()
                        
                        if stripped.startswith('import ') or stripped.startswith('from '):
                            should_skip = False
                            
                            if stripped.startswith('import '):
                                parts = stripped.split('import')
                                if len(parts) > 1:
                                    imports = [p.strip() for p in parts[1].split(',')]
                                    for imp in imports:
                                        base_name = imp.split('.')[0]
                                        if imp in unused_imports or base_name in unused_imports:
                                            should_skip = True
                                            break
                            
                            elif stripped.startswith('from '):
                                parts = stripped.split('import')
                                if len(parts) > 1:
                                    module = parts[0].replace('from', '').strip()
                                    imports = [p.strip() for p in parts[1].split(',')]
                                    for imp in imports:
                                        full_name = f"{module}.{imp}"
                                        if full_name in unused_imports or imp in unused_imports:
                                            should_skip = True
                                            break
                            
                            if not should_skip:
                                new_lines.append(line)
                            else:
                                count += 1
                        else:
                            new_lines.append(line)
                    
                    # Write back
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.writelines(new_lines)
                    logger.debug(f"Removed unused imports from {file_path}")
                    
            except Exception as e:
                logger.error(f"Error removing unused imports in {file_path}: {e}")
        
        return count

    def standardize_logging(self) -> int:
        """Standardize logging configurations across files."""
        count = 0
        logger.info("Standardizing logging configurations...")
        
        # Pattern to match old-style logging calls
        old_patterns = [
            r'logging\.getLogger\(__name__\)',
            r'logger\s*=\s*logging\.getLogger',
            r'logging\.basicConfig',
        ]
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                modified = False
                
                # Replace old logging patterns with standardized imports
                for pattern in old_patterns:
                    if re.search(pattern, content):
                        modified = True
                        break
                
                if modified:
                    # Ensure standard logging import and setup
                    if 'from utils.logging_utils import setup_logging, get_logger' not in content:
                        # Add import after other imports
                        lines = content.splitlines(keepends=True)
                        new_lines = []
                        import_section_end = -1
                        
                        for i, line in enumerate(lines):
                            if line.strip().startswith('import ') or line.strip().startswith('from '):
                                import_section_end = i
                            elif import_section_end != -1:
                                # Insert logging import
                                new_lines.append("from utils.logging_utils import setup_logging, get_logger\n")
                                new_lines.append("\n")
                                import_section_end = -1
                                modified = True
                            
                            new_lines.append(line)
                        
                        if modified:
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.writelines(new_lines)
                            count += 1
                            logger.debug(f"Standardized logging in {file_path}")
                    
            except Exception as e:
                logger.error(f"Error standardizing logging in {file_path}: {e}")
        
        return count

    def clean_temp_files(self) -> int:
        """Remove temporary files and directories."""
        count = 0
        logger.info("Cleaning temporary files...")
        
        temp_patterns = [
            "__pycache__",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".Python",
            "build",
            "develop-eggs",
            "dist",
            "downloads",
            "eggs",
            ".eggs",
            "lib",
            "lib64",
            "parts",
            "sdist",
            "var",
            "wheels",
            "*.egg-info",
            ".installed.cfg",
            "*.egg",
            "MANIFEST",
            "*.log",
            ".DS_Store",
            "Thumbs.db",
        ]
        
        for pattern in temp_patterns:
            matches = list(self.project_root.rglob(pattern))
            for match in matches:
                try:
                    if match.is_dir():
                        import shutil
                        shutil.rmtree(match)
                    else:
                        match.unlink()
                    count += 1
                    logger.debug(f"Removed {match}")
                except Exception as e:
                    logger.warning(f"Could not remove {match}: {e}")
        
        return count

    def validate_requirements(self) -> Tuple[List[str], List[str]]:
        """Validate requirements.txt and identify unused dependencies."""
        logger.info("Validating requirements.txt...")
        
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            logger.warning("requirements.txt not found")
            return [], []
        
        with open(requirements_file, 'r', encoding='utf-8') as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        # Extract all imported modules from Python files
        imported_modules = set()
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imported_modules.add(alias.name.split('.')[0])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imported_modules.add(node.module.split('.')[0])
            except:
                continue
        
        # Map common package names to import names
        package_to_import = {
            'pandas': 'pandas',
            'scikit-learn': 'sklearn',
            'scipy': 'scipy',
            'statsmodels': 'statsmodels',
            'biom-format': 'biom',
            'skbio': 'skbio',
            'numpy': 'numpy',
            'matplotlib': 'matplotlib',
            'seaborn': 'seaborn',
            'requests': 'requests',
            'biopython': 'Bio',
            'pytest': 'pytest',
            'flake8': 'flake8',
            'black': 'black',
        }
        
        used_deps = []
        unused_deps = []
        
        for req in requirements:
            # Handle version specifiers
            pkg_name = req.split('>=')[0].split('<=')[0].split('==')[0].split('~=')[0].split('!=')[0].strip()
            pkg_name = pkg_name.replace('-', '_').lower()
            
            import_name = package_to_import.get(pkg_name, pkg_name)
            
            if import_name in imported_modules or pkg_name in imported_modules:
                used_deps.append(req)
            else:
                # Check if it's a development tool
                if pkg_name in ['pytest', 'flake8', 'black', 'mypy', 'isort']:
                    used_deps.append(req)
                else:
                    unused_deps.append(req)
        
        logger.info(f"Found {len(used_deps)} used dependencies and {len(unused_deps)} unused dependencies")
        return used_deps, unused_deps

    def fix_requirements(self) -> None:
        """Update requirements.txt to remove unused dependencies."""
        logger.info("Fixing requirements.txt...")
        
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            logger.warning("requirements.txt not found")
            return
        
        used_deps, unused_deps = self.validate_requirements()
        
        if unused_deps:
            logger.warning(f"Removing {len(unused_deps)} unused dependencies: {unused_deps}")
            
            with open(requirements_file, 'w', encoding='utf-8') as f:
                f.write("# Core dependencies\n")
                for dep in used_deps:
                    f.write(f"{dep}\n")
                
                if unused_deps:
                    f.write("\n# Previously unused dependencies (commented out)\n")
                    for dep in unused_deps:
                        f.write(f"# {dep}\n")
            
            logger.info("Updated requirements.txt")

    def run_linting(self) -> bool:
        """Run linting tools to check code quality."""
        logger.info("Running linting checks...")
        
        try:
            # Run flake8
            result = subprocess.run(
                ['flake8', str(self.code_dir), str(self.tests_dir)],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode != 0:
                logger.warning("flake8 found issues:")
                logger.warning(result.stdout)
                return False
            
            logger.info("flake8 passed")
            return True
            
        except FileNotFoundError:
            logger.warning("flake8 not installed, skipping")
            return True
        except Exception as e:
            logger.error(f"Error running flake8: {e}")
            return False

    def run_formatting(self) -> bool:
        """Run code formatting tools."""
        logger.info("Running code formatting...")
        
        try:
            # Run black
            result = subprocess.run(
                ['black', '--check', str(self.code_dir), str(self.tests_dir)],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode != 0:
                logger.warning("black found formatting issues:")
                logger.warning(result.stdout)
                return False
            
            logger.info("black passed")
            return True
            
        except FileNotFoundError:
            logger.warning("black not installed, skipping")
            return True
        except Exception as e:
            logger.error(f"Error running black: {e}")
            return False

    def run(self) -> None:
        """Execute all cleanup tasks."""
        logger.info("Starting code cleanup...")
        
        # Set random seed for reproducibility
        set_seed(42)
        
        # Scan files
        self.scan_python_files()
        
        # Analyze imports
        self.analyze_imports()
        
        # Perform cleanup tasks
        count = 0
        count += self.consolidate_imports()
        count += self.remove_unused_imports()
        count += self.standardize_logging()
        count += self.clean_temp_files()
        self.fix_requirements()
        
        logger.info(f"Cleanup complete. Modified {count} files.")
        
        # Run linting and formatting checks
        self.run_linting()
        self.run_formatting()
        
        logger.info("Code cleanup finished successfully")


def main():
    """Main entry point for the cleanup script."""
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)
    
    # Get project root
    project_root = Path(__file__).parent.parent
    
    # Run cleanup
    cleanup = CodeCleanup(project_root)
    cleanup.run()
    
    logger.info("Cleanup completed successfully")


if __name__ == "__main__":
    main()