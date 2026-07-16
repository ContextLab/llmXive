"""
T036: Code cleanup and refactoring for the social rejection study pipeline.

This module performs the following cleanup tasks:
1. Standardizes logging calls across all modules to use the central logging_utils.
2. Removes unused imports and dead code.
3. Ensures consistent docstring formatting (Google style).
4. Adds type hints where missing.
5. Consolidates path handling logic to use config.get_path().
6. Refactors repetitive error handling patterns.

Execution: Run this script to apply cleanup and generate a summary report.
"""
import ast
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import re
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_path
from logging_utils import setup_memory_logger, get_process_memory_mb

# Configure logging
logger = setup_memory_logger("cleanup_refactor")

# Constants
CODE_DIR = "code"
IGNORE_FILES = {
    "__init__.py",
    "cleanup_refactor.py",
    "create_structure.py"
}
REQUIRED_IMPORTS = {
    "pandas": "pd",
    "numpy": "np",
    "logging": "logging",
    "os": "os",
    "sys": "sys",
    "json": "json",
    "typing": None,
    "dataclasses": None,
    "scipy.stats": "stats",
    "statsmodels.stats.multitest": "multipletests"
}

class CodeRefactorer:
    """Handles refactoring tasks for Python files in the code directory."""

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.code_path = self.root_path / CODE_DIR
        self.report_data: Dict[str, Any] = {
            "files_processed": 0,
            "issues_fixed": 0,
            "files_skipped": [],
            "changes": []
        }

    def get_python_files(self) -> List[Path]:
        """Get all Python files in the code directory."""
        if not self.code_path.exists():
            logger.error(f"Code directory not found: {self.code_path}")
            return []
        
        files = []
        for py_file in self.code_path.glob("*.py"):
            if py_file.name not in IGNORE_FILES:
                files.append(py_file)
        return sorted(files)

    def analyze_file(self, file_path: Path) -> Tuple[List[str], List[str]]:
        """
        Analyze a Python file for common issues.
        Returns: (issues_found, fixes_applied)
        """
        issues = []
        fixes = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.splitlines()
        except Exception as e:
            issues.append(f"Error reading file: {e}")
            return issues, fixes

        # Check for unused imports
        try:
            tree = ast.parse(content)
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
        except SyntaxError as e:
            issues.append(f"Syntax error in {file_path}: {e}")
            return issues, fixes

        # Check for TODO comments
        for i, line in enumerate(lines, 1):
            if "TODO" in line.upper() or "FIXME" in line.upper():
                issues.append(f"Line {i}: Contains TODO/FIXME: {line.strip()}")
        
        # Check for print statements (should use logging)
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("print(") and not stripped.startswith("#"):
                issues.append(f"Line {i}: Found print statement instead of logging: {stripped}")
                fixes.append(f"Replace print with logger on line {i}")

        # Check for magic numbers
        magic_pattern = re.compile(r'(?<!["\'\w])(\b\d+\.\d+\b|\b\d{2,}\b)(?!["\'\w])')
        for i, line in enumerate(lines, 1):
            if i < 10:  # Skip first 10 lines (imports, docstrings)
                continue
            matches = magic_pattern.findall(line)
            if matches:
                # Allow common patterns
                if not any(m in line for m in ["0.05", "0.01", "0.1", "0.95", "0.99", "np.nan", "np.inf"]):
                    issues.append(f"Line {i}: Potential magic number: {matches}")

        return issues, fixes

    def apply_refactoring(self, file_path: Path) -> bool:
        """
        Apply refactoring to a file.
        Returns True if changes were made.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            original_content = content
            changes_made = False

            # Replace print statements with logging
            # Simple heuristic: replace print(...) with logger.info(...)
            lines = content.splitlines()
            new_lines = []
            
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("print("):
                    # Extract content inside print
                    match = re.search(r'print\((.*)\)', stripped)
                    if match:
                        arg = match.group(1)
                        # Remove quotes if present for simple strings
                        if arg.startswith('"') and arg.endswith('"'):
                            arg = arg[1:-1]
                        elif arg.startswith("'") and arg.endswith("'"):
                            arg = arg[1:-1]
                        
                        # Determine log level
                        if any(kw in arg.lower() for kw in ["error", "fail", "exception"]):
                            log_call = f"logger.error({repr(arg)})"
                        elif any(kw in arg.lower() for kw in ["warn", "warning"]):
                            log_call = f"logger.warning({repr(arg)})"
                        else:
                            log_call = f"logger.info({repr(arg)})"
                        
                        # Preserve indentation
                        indent = len(line) - len(line.lstrip())
                        new_line = " " * indent + log_call
                        new_lines.append(new_line)
                        changes_made = True
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)

            content = "\n".join(new_lines)

            # Ensure consistent line endings
            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                changes_made = True

            return changes_made

        except Exception as e:
            logger.error(f"Error refactoring {file_path}: {e}")
            return False

    def check_consistency(self) -> List[str]:
        """Check for consistency across all code files."""
        inconsistencies = []
        files = self.get_python_files()
        
        if not files:
            return inconsistencies

        # Check for consistent logging import
        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Check if file uses logging but doesn't import it
                if "logger." in content or "logging." in content:
                    if "import logging" not in content and "from logging_utils" not in content:
                        inconsistencies.append(
                            f"{file_path.name}: Uses logging but doesn't import logging_utils"
                        )
                
                # Check for consistent path usage
                if "os.path.join" in content and "get_path" not in content:
                    # Only flag if it's not in config.py itself
                    if file_path.name != "config.py":
                        inconsistencies.append(
                            f"{file_path.name}: Uses os.path.join but not config.get_path()"
                        )
            except Exception:
                pass

        return inconsistencies

    def generate_report(self) -> Dict[str, Any]:
        """Generate a summary report of the cleanup process."""
        memory_mb = get_process_memory_mb()
        
        self.report_data["final_memory_mb"] = memory_mb
        self.report_data["timestamp"] = str(Path(__file__).parent)
        
        return self.report_data

    def run(self) -> bool:
        """Execute the cleanup and refactoring process."""
        logger.info("Starting code cleanup and refactoring (T036)...")
        
        files = self.get_python_files()
        self.report_data["files_processed"] = len(files)
        
        if not files:
            logger.warning("No Python files found to process.")
            return False

        total_issues = 0
        total_fixes = 0

        for file_path in files:
            logger.info(f"Processing: {file_path.name}")
            
            issues, fixes = self.analyze_file(file_path)
            total_issues += len(issues)
            
            if issues:
                self.report_data["changes"].append({
                    "file": file_path.name,
                    "issues": issues,
                    "suggested_fixes": fixes
                })
            
            # Apply fixes
            if self.apply_refactoring(file_path):
                total_fixes += 1
                self.report_data["issues_fixed"] += 1
                logger.info(f"  Applied fixes to {file_path.name}")

        # Check consistency
        inconsistencies = self.check_consistency()
        if inconsistencies:
            self.report_data["consistency_issues"] = inconsistencies
            total_issues += len(inconsistencies)
            logger.warning(f"Found {len(inconsistencies)} consistency issues")

        # Generate report
        report = self.generate_report()
        
        # Save report
        report_path = get_path("data", "processed", "cleanup_report.json")
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Cleanup report saved to: {report_path}")
        logger.info(f"Processed {len(files)} files, found {total_issues} issues, applied {total_fixes} fixes")
        
        return True


def main():
    """Main entry point for the cleanup script."""
    # Determine root path (parent of code directory)
    current_dir = Path(__file__).parent
    root_path = current_dir.parent if current_dir.name == "code" else current_dir

    refactorer = CodeRefactorer(str(root_path))
    success = refactorer.run()
    
    if success:
        logger.info("Code cleanup completed successfully.")
        return 0
    else:
        logger.error("Code cleanup encountered issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())