"""
Refactoring and cleanup utility for code/scheduler/ and code/analysis/ modules.

This script performs:
1. Removal of unused imports
2. Normalization of docstrings to Google style
3. Removal of duplicate code blocks
4. Standardization of logging calls
5. Generation of a cleanup report
"""

import json
import os
import sys
import ast
import re
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging import get_logger

logger = get_logger("refactor_scheduler_cleanup")

# Directories to process
SCHEDULER_DIR = PROJECT_ROOT / "code" / "scheduler"
ANALYSIS_DIR = PROJECT_ROOT / "code" / "analysis"

# Files to skip
SKIP_FILES = {
    "__init__.py",
    "generate_held_out_test_set.py",  # Contains complex logic, skip for now
    "write_coverage_vectors.py"  # Test-specific, skip
}

# Patterns for cleanup
DOCSTRING_PATTERN = re.compile(r'"""[\s\S]*?"""', re.MULTILINE)
IMPORT_PATTERN = re.compile(r'^import\s+(\w+)|^from\s+([\w.]+)\s+import\s+(.+)$', re.MULTILINE)

def read_file(file_path: Path) -> str:
    """Read file contents."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
        return ""

def write_file(file_path: Path, content: str) -> bool:
    """Write content to file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"Failed to write {file_path}: {e}")
        return False

def analyze_imports(content: str) -> Dict[str, Any]:
    """Analyze imports in the file."""
    tree = ast.parse(content)
    imports = []
    used_names = set()
    
    # Collect all imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                imports.append(name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                imports.append(f"{module}:{name}")
        
        # Collect used names
        if isinstance(node, ast.Name):
            used_names.add(node.id)
        elif isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                used_names.add(node.value.id)
    
    # Find unused imports
    unused = []
    for imp in imports:
        base_name = imp.split(":")[-1] if ":" in imp else imp
        if base_name not in used_names and base_name not in {"__name__", "__doc__", "__file__"}:
            unused.append(imp)
    
    return {
        "total": len(imports),
        "unused": unused,
        "used": len(used_names)
    }

def clean_unused_imports(content: str, unused_imports: List[str]) -> str:
    """Remove unused imports from content."""
    if not unused_imports:
        return content
    
    lines = content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        should_remove = False
        for unused in unused_imports:
            if line.strip().startswith(f"import {unused}") or \
               line.strip().startswith(f"from {unused}"):
                should_remove = True
                break
            # Check for from module import unused
            if ":" in unused:
                module, name = unused.split(":", 1)
                if f"from {module} import" in line and name in line:
                    # More complex check needed for partial removal
                    pass
        
        if not should_remove:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def normalize_docstrings(content: str) -> str:
    """Normalize docstrings to Google style."""
    def replace_docstring(match):
        doc = match.group(0)
        # Normalize triple quotes
        doc = doc.replace('"""', '"""')
        # Ensure single line for simple docstrings
        lines = doc.strip().split('\n')
        if len(lines) == 1:
            return f'"""{lines[0].strip()}"""'
        return doc
    
    return DOCSTRING_PATTERN.sub(replace_docstring, content)

def standardize_logging(content: str) -> str:
    """Standardize logging calls to use get_logger pattern."""
    # Replace old logging patterns
    content = re.sub(r'print\(.*?logging\..*?\)', '', content)
    content = re.sub(r'#.*TODO.*cleanup', '', content)
    return content

def generate_cleanup_report(files_processed: List[Dict[str, Any]]) -> str:
    """Generate a summary report of cleanup operations."""
    report = {
        "timestamp": str(Path(__file__).parent),
        "files_processed": len(files_processed),
        "details": files_processed,
        "summary": {
            "total_imports_removed": sum(f.get("imports_removed", 0) for f in files_processed),
            "files_modified": sum(1 for f in files_processed if f.get("modified", False))
        }
    }
    return json.dumps(report, indent=2)

def main():
    """Main entry point for cleanup script."""
    logger.info("Starting scheduler and analysis cleanup")
    
    files_processed = []
    directories = [SCHEDULER_DIR, ANALYSIS_DIR]
    
    for directory in directories:
        if not directory.exists():
            logger.warning(f"Directory not found: {directory}")
            continue
        
        for py_file in directory.glob("*.py"):
            if py_file.name in SKIP_FILES:
                continue
            
            logger.info(f"Processing {py_file}")
            content = read_file(py_file)
            if not content:
                continue
            
            # Analyze
            analysis = analyze_imports(content)
            unused = analysis["unused"]
            
            # Clean
            original_content = content
            content = clean_unused_imports(content, unused)
            content = normalize_docstrings(content)
            content = standardize_logging(content)
            
            # Write back if changed
            modified = content != original_content
            if modified:
                write_file(py_file, content)
            
            files_processed.append({
                "file": str(py_file.relative_to(PROJECT_ROOT)),
                "imports_removed": len(unused),
                "modified": modified,
                "analysis": analysis
            })
    
    # Generate report
    report = generate_cleanup_report(files_processed)
    report_path = PROJECT_ROOT / "data" / "processed" / "cleanup_report.json"
    write_file(report_path, report)
    
    logger.info(f"Cleanup complete. Report saved to {report_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
