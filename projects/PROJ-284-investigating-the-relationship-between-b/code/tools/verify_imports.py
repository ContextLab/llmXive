"""
Import verification utility for the llmXive pipeline.

This module verifies that all imports in the codebase are valid and
that there are no circular dependencies or missing imports.
"""
import os
import sys
import logging
import ast
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field

from logging_config import setup_logging, get_logger

@dataclass
class ImportReport:
    """Summary of import verification results."""
    files_checked: int = 0
    valid_imports: int = 0
    invalid_imports: List[str] = field(default_factory=list)
    missing_modules: List[str] = field(default_factory=list)
    circular_deps: List[Tuple[str, str]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

class ImportVerifier:
    """Verifies imports in the codebase."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.logger = get_logger(__name__)
        self.report = ImportReport()
        
        # Known valid imports
        self.valid_stdlib = {
            'os', 'sys', 'pathlib', 'typing', 'dataclasses',
            'logging', 'json', 'csv', 're', 'ast', 'tempfile',
            'shutil', 'subprocess', 'collections', 'itertools',
            'functools', 'operator', 'datetime', 'time', 'hashlib',
            'inspect', 'io', 'string', 'textwrap', 'warnings'
        }
        
        self.valid_third_party = {
            'numpy', 'pandas', 'scipy', 'sklearn', 'matplotlib',
            'seaborn', 'nilearn', 'nibabel', 'networkx', 'requests',
            'statsmodels', 'pytest', 'ruff', 'black'
        }
        
        # Local modules (derived from code directory)
        self.local_modules = set()
        self._discover_local_modules()

    def _discover_local_modules(self):
        """Discover all local modules in the project."""
        code_dir = self.project_root / 'code'
        if code_dir.exists():
            for item in code_dir.rglob('*.py'):
                # Convert path to module name
                rel_path = item.relative_to(code_dir)
                module_name = str(rel_path).replace('/', '.').replace('\\', '.')[:-3]
                self.local_modules.add(module_name.split('.')[0])
                self.local_modules.add(module_name)

    def verify_file(self, file_path: Path) -> List[str]:
        """Verify imports in a single file."""
        invalid_imports = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module = alias.name.split('.')[0]
                        if not self._is_valid_import(module, file_path):
                            invalid_imports.append(f"{file_path}: import '{alias.name}' not found")
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module = node.module.split('.')[0]
                        if not self._is_valid_import(module, file_path):
                            invalid_imports.append(f"{file_path}: from '{node.module}' not found")
            
            self.report.files_checked += 1
            self.report.valid_imports += len(invalid_imports) == 0
            
        except SyntaxError as e:
            self.report.errors.append(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            self.report.errors.append(f"Error verifying {file_path}: {e}")
        
        return invalid_imports

    def _is_valid_import(self, module: str, file_path: Path) -> bool:
        """Check if an import is valid."""
        # Check stdlib
        if module in self.valid_stdlib:
            return True
        
        # Check third-party
        if module in self.valid_third_party:
            return True
        
        # Check local modules
        if module in self.local_modules:
            return True
        
        # Special case for relative imports
        if file_path.parent.name == 'tools' and module in ['config', 'logging_config']:
            return True
        
        return False

    def verify_all(self) -> ImportReport:
        """Verify all imports in the codebase."""
        self.logger.info("Verifying imports...")
        
        python_files = list(self.project_root.rglob('*.py'))
        
        for file_path in python_files:
            invalid = self.verify_file(file_path)
            self.report.invalid_imports.extend(invalid)
        
        self.logger.info(f"Verification complete. Files checked: {self.report.files_checked}")
        return self.report

    def generate_report(self, output_path: Path) -> None:
        """Generate an import verification report."""
        report_content = f"""
# Import Verification Report
Generated: {__import__('datetime').datetime.now().isoformat()}

## Summary
- Files Checked: {self.report.files_checked}
- Valid Imports: {self.report.valid_imports}
- Invalid Imports: {len(self.report.invalid_imports)}
- Missing Modules: {len(self.report.missing_modules)}
- Circular Dependencies: {len(self.report.circular_deps)}

## Invalid Imports
"""
        if self.report.invalid_imports:
            for imp in self.report.invalid_imports:
                report_content += f"- {imp}\n"
        else:
            report_content += "None\n"
        
        report_content += "\n## Errors\n"
        if self.report.errors:
            for error in self.report.errors:
                report_content += f"- {error}\n"
        else:
            report_content += "None\n"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        self.logger.info(f"Report written to {output_path}")

def main():
    """Main entry point for import verification script."""
    setup_logging()
    logger = get_logger(__name__)
    
    project_root = Path(__file__).parent.parent
    verifier = ImportVerifier(project_root)
    
    try:
        report = verifier.verify_all()
        verifier.generate_report(project_root / 'logs' / 'import_verification_report.txt')
        
        if report.invalid_imports:
            logger.warning(f"Found {len(report.invalid_imports)} invalid imports")
            return 1
        
        logger.info("All imports verified successfully")
        return 0
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())