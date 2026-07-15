"""
Code cleanup and refactoring utilities.

Provides functions to standardize code, remove unused imports,
normalize constants, and improve overall code quality.
"""
import ast
import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class CodeCleanupReport:
    """Report of code cleanup operations performed."""
    files_processed: int = 0
    files_modified: int = 0
    imports_standardized: int = 0
    unused_imports_removed: int = 0
    constants_normalized: int = 0
    issues_found: List[str] = field(default_factory=list)
    issues_fixed: List[str] = field(default_factory=list)

def standardize_imports(source_code: str) -> Tuple[str, int]:
    """
    Standardize import statements in source code.
    
    Args:
        source_code: Python source code
        
    Returns:
        Tuple of (cleaned source code, number of changes made)
    """
    changes = 0
    lines = source_code.split('\n')
    
    # Group imports by type
    stdlib_imports = []
    third_party_imports = []
    local_imports = []
    other_lines = []
    
    in_import_block = False
    current_imports = []
    
    for line in lines:
        stripped = line.strip()
        
        if stripped.startswith('import ') or stripped.startswith('from '):
            current_imports.append(line)
            in_import_block = True
        elif in_import_block and (stripped.startswith('import ') or stripped.startswith('from ') or stripped == ''):
            if stripped == '':
                # End of import block
                if current_imports:
                  # Sort and deduplicate
                  current_imports.sort()
                  unique_imports = []
                  seen = set()
                  for imp in current_imports:
                      if imp not in seen:
                          unique_imports.append(imp)
                          seen.add(imp)
                  
                  # Categorize
                  for imp in unique_imports:
                      if imp.strip().startswith('from ') or imp.strip().startswith('import '):
                          module = imp.strip()
                          if 'analysis.' in module or 'data.' in module or 'utils.' in module or 'viz.' in module:
                              local_imports.append(imp)
                          elif any(pkg in module for pkg in ['pandas', 'numpy', 'sklearn', 'statsmodels', 'matplotlib', 'seaborn', 'requests', 'yaml', 'tqdm', 'joblib', 'pyarrow']):
                              third_party_imports.append(imp)
                          else:
                              stdlib_imports.append(imp)
                  
                  current_imports = []
                in_import_block = False
            else:
                current_imports.append(line)
        else:
            if in_import_block and current_imports:
                # Process the import block
                current_imports.sort()
                unique_imports = []
                seen = set()
                for imp in current_imports:
                    if imp not in seen:
                        unique_imports.append(imp)
                        seen.add(imp)
                
                # Categorize
                for imp in unique_imports:
                    module = imp.strip()
                    if 'analysis.' in module or 'data.' in module or 'utils.' in module or 'viz.' in module or 'validation.' in module:
                        local_imports.append(imp)
                    elif any(pkg in module for pkg in ['pandas', 'numpy', 'sklearn', 'statsmodels', 'matplotlib', 'seaborn', 'requests', 'yaml', 'tqdm', 'joblib', 'pyarrow', 'parquet', 'geopandas']):
                        third_party_imports.append(imp)
                    else:
                        stdlib_imports.append(imp)
                
                current_imports = []
                in_import_block = False
            
            other_lines.append(line)
    
    # Process remaining imports if any
    if current_imports:
        current_imports.sort()
        unique_imports = []
        seen = set()
        for imp in current_imports:
            if imp not in seen:
                unique_imports.append(imp)
                seen.add(imp)
        
        for imp in unique_imports:
            module = imp.strip()
            if 'analysis.' in module or 'data.' in module or 'utils.' in module or 'viz.' in module:
                local_imports.append(imp)
            elif any(pkg in module for pkg in ['pandas', 'numpy', 'sklearn', 'statsmodels', 'matplotlib', 'seaborn', 'requests', 'yaml', 'tqdm', 'joblib', 'pyarrow']):
                third_party_imports.append(imp)
            else:
                stdlib_imports.append(imp)
    
    # Reconstruct with standard ordering
    cleaned_lines = []
    
    if stdlib_imports:
        cleaned_lines.extend(stdlib_imports)
        cleaned_lines.append('')
    
    if third_party_imports:
        cleaned_lines.extend(third_party_imports)
        cleaned_lines.append('')
    
    if local_imports:
        cleaned_lines.extend(local_imports)
        cleaned_lines.append('')
    
    cleaned_lines.extend(other_lines)
    
    # Count changes
    if len(cleaned_lines) != len(lines) or ''.join(cleaned_lines) != source_code:
        changes = 1
    
    return '\n'.join(cleaned_lines), changes


def remove_unused_imports(source_code: str) -> Tuple[str, int]:
    """
    Remove unused import statements from source code.
    
    Args:
        source_code: Python source code
        
    Returns:
        Tuple of (cleaned source code, number of imports removed)
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        logger.warning(f"Syntax error in source code: {e}")
        return source_code, 0
    
    # Collect all used names
    used_names = set()
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used_names.add(node.id)
        elif isinstance(node, ast.Attribute):
            # Handle module.attribute access
            if isinstance(node.value, ast.Name):
                used_names.add(node.value.id)
    
    # Find imports
    lines = source_code.split('\n')
    new_lines = []
    removed_count = 0
    
    for line in lines:
        stripped = line.strip()
        
        if stripped.startswith('import ') or stripped.startswith('from '):
            # Parse the import
            try:
                if stripped.startswith('import '):
                    # Simple import: import module
                    module_name = stripped.replace('import ', '').strip()
                    if module_name in used_names or any(module_name.startswith(u + '.') for u in used_names):
                        new_lines.append(line)
                    else:
                        removed_count += 1
                        logger.debug(f"Removed unused import: {module_name}")
                elif stripped.startswith('from '):
                    # From import: from module import name
                    parts = stripped.replace('from ', '').split(' import ')
                    if len(parts) == 2:
                        module, names = parts
                        name_list = [n.strip().split(' as ')[0] for n in names.split(',')]
                        
                        # Check if any name is used
                        if any(name in used_names for name in name_list):
                            new_lines.append(line)
                        else:
                            removed_count += 1
                            logger.debug(f"Removed unused from import: {stripped}")
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            except Exception as e:
                logger.warning(f"Error parsing import line: {stripped} - {e}")
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    return '\n'.join(new_lines), removed_count


def normalize_constants(source_code: str) -> Tuple[str, int]:
    """
    Normalize numeric constants in source code.
    
    Args:
        source_code: Python source code
        
    Returns:
        Tuple of (cleaned source code, number of constants normalized)
    """
    changes = 0
    
    # Common patterns to normalize
    patterns = [
        (r'\b1024\s*\*\s*1024\s*\*\s*1024\b', '(1024**3)'),  # 1 GB in bytes
        (r'\b1024\s*\*\s*1024\b', '(1024**2)'),  # 1 MB in bytes
        (r'\b1\.0\s*\/\s*100\b', '0.01'),  # Percentages
        (r'\b1000000\b', '1_000_000'),  # Large numbers with underscores
    ]
    
    new_code = source_code
    for pattern, replacement in patterns:
        matches = re.findall(pattern, new_code)
        if matches:
            new_code = re.sub(pattern, replacement, new_code)
            changes += len(matches)
    
    return new_code, changes


def run_code_cleanup(code_dir: Path) -> CodeCleanupReport:
    """
    Run code cleanup on all Python files in a directory.
    
    Args:
        code_dir: Directory containing Python files
        
    Returns:
        Cleanup report
    """
    report = CodeCleanupReport()
    
    python_files = list(code_dir.rglob('*.py'))
    report.files_processed = len(python_files)
    
    logger.info(f"Processing {len(python_files)} Python files in {code_dir}")
    
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            original_code = source_code
            changes_made = False
            
            # Standardize imports
            source_code, import_changes = standardize_imports(source_code)
            if import_changes > 0:
                report.imports_standardized += import_changes
                changes_made = True
            
            # Remove unused imports
            source_code, unused_changes = remove_unused_imports(source_code)
            if unused_changes > 0:
                report.unused_imports_removed += unused_changes
                changes_made = True
            
            # Normalize constants
            source_code, const_changes = normalize_constants(source_code)
            if const_changes > 0:
                report.constants_normalized += const_changes
                changes_made = True
            
            # Write back if changed
            if changes_made and source_code != original_code:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(source_code)
                report.files_modified += 1
                report.issues_fixed.append(f"Cleaned {py_file}")
            
        except Exception as e:
            error_msg = f"Error processing {py_file}: {e}"
            report.issues_found.append(error_msg)
            logger.error(error_msg)
    
    return report


def main():
    """Main entry point for code cleanup."""
    logger.info("Starting code cleanup...")
    
    # Determine code directory
    code_dir = Path(__file__).parent
    if not code_dir.exists():
        logger.error(f"Code directory not found: {code_dir}")
        return None
    
    # Run cleanup
    report = run_code_cleanup(code_dir)
    
    # Print report
    print("\n" + "="*60)
    print("CODE CLEANUP REPORT")
    print("="*60)
    print(f"Files processed: {report.files_processed}")
    print(f"Files modified: {report.files_modified}")
    print(f"Imports standardized: {report.imports_standardized}")
    print(f"Unused imports removed: {report.unused_imports_removed}")
    print(f"Constants normalized: {report.constants_normalized}")
    
    if report.issues_found:
        print(f"\nIssues found: {len(report.issues_found)}")
        for issue in report.issues_found[:10]:  # Show first 10
            print(f"  - {issue}")
    
    if report.issues_fixed:
        print(f"\nIssues fixed: {len(report.issues_fixed)}")
    
    print("="*60)
    
    return report


if __name__ == "__main__":
    main()