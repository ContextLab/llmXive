import ast
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

class CodeRefactorer:
    """Utility class for code cleanup and refactoring."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.code_dir = self.project_root / "code"
        
    def find_python_files(self) -> List[Path]:
        """Find all Python files in the code directory."""
        return list(self.code_dir.glob("**/*.py"))
    
    def check_syntax(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """Check if a Python file has valid syntax."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                ast.parse(f.read())
            return True, None
        except SyntaxError as e:
            return False, str(e)
    
    def refactor_all(self) -> Dict[str, str]:
        """
        Refactor all Python files in the code directory.
        
        Returns:
            Dictionary mapping file paths to status messages
        """
        results = {}
        
        for py_file in self.find_python_files():
            is_valid, error = self.check_syntax(py_file)
            if is_valid:
                results[str(py_file)] = "OK"
            else:
                results[str(py_file)] = f"SYNTAX_ERROR: {error}"
        
        return results

def main():
    """Main entry point for code cleanup and refactoring."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    refactoring = CodeRefactorer(project_root)
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting code cleanup and refactoring...")
    
    results = refactoring.refactor_all()
    
    for file_path, status in results.items():
        if status == "OK":
            logger.info(f"✓ {file_path}")
        else:
            logger.error(f"✗ {file_path}: {status}")
    
    # Summary
    ok_count = sum(1 for s in results.values() if s == "OK")
    error_count = len(results) - ok_count
    
    logger.info(f"\nSummary: {ok_count} files OK, {error_count} files with errors")
    
    return 0 if error_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
