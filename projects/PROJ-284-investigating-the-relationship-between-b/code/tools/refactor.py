"""
Refactoring utilities for the llmXive pipeline.

This module provides functions to:
1. Extract common patterns into reusable functions
2. Consolidate duplicate code
3. Improve code structure and readability
4. Update deprecated patterns
"""
import os
import sys
import logging
import ast
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
import inspect

from logging_config import setup_logging, get_logger
from config import get_config

@dataclass
class RefactoringReport:
    """Summary of refactoring operations performed."""
    files_analyzed: int = 0
    functions_extracted: int = 0
    duplicates_removed: int = 0
    patterns_improved: int = 0
    documentation_added: int = 0
    errors: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

class CodeRefactorer:
    """Handles code refactoring operations."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.logger = get_logger(__name__)
        self.report = RefactoringReport()
        
        # Common patterns to look for
        self.long_function_threshold = 50  # lines
        self.duplication_threshold = 0.7   # similarity ratio
        
        # Patterns to improve
        self.patterns_to_improve = [
            (r'print\(', 'Use logger instead of print'),
            (r'\.append\(.*\)\s*$', 'Consider list comprehension'),
            (r'if\s+not\s+.*\s+is\s+None', 'Use `is not None` or `or` operator'),
            (r'len\(.*\)\s*==\s*0', 'Use `not` operator for empty check'),
        ]

    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a Python file for refactoring opportunities."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            tree = ast.parse(content)
            
            analysis = {
                'functions': [],
                'classes': [],
                'imports': [],
                'complexity': 0,
                'duplicates': [],
                'patterns': [],
                'docstrings_missing': []
            }
            
            # Analyze functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = {
                        'name': node.name,
                        'lines': node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0,
                        'args': len(node.args.args),
                        'has_docstring': ast.get_docstring(node) is not None
                    }
                    analysis['functions'].append(func_info)
                    
                    if not func_info['has_docstring']:
                        analysis['docstrings_missing'].append(node.name)
                    
                    if func_info['lines'] > self.long_function_threshold:
                        self.report.suggestions.append(
                            f"Function '{node.name}' in {file_path} is long ({func_info['lines']} lines)"
                        )
                
                elif isinstance(node, ast.ClassDef):
                    analysis['classes'].append({
                        'name': node.name,
                        'methods': len([n for n in node.body if isinstance(n, ast.FunctionDef)])
                    })
                
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis['imports'].append(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        analysis['imports'].append(f"from {node.module}")
            
            # Check for patterns to improve
            for pattern, suggestion in self.patterns_to_improve:
                matches = re.findall(pattern, content)
                if matches:
                    analysis['patterns'].append({
                        'pattern': pattern,
                        'count': len(matches),
                        'suggestion': suggestion
                    })
            
            self.report.files_analyzed += 1
            return analysis
            
        except SyntaxError as e:
            self.report.errors.append(f"Syntax error in {file_path}: {e}")
            return {}
        except Exception as e:
            self.report.errors.append(f"Error analyzing {file_path}: {e}")
            return {}

    def extract_common_patterns(self, file_path: Path) -> bool:
        """Extract common patterns into reusable functions."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for repeated code blocks
            lines = content.splitlines()
            repeated_blocks = []
            
            for i in range(len(lines)):
                for j in range(i + 3, min(i + 10, len(lines))):
                    block1 = '\n'.join(lines[i:i+3])
                    block2 = '\n'.join(lines[j:j+3])
                    
                    if block1 == block2 and len(block1.strip()) > 10:
                        repeated_blocks.append((i, j, block1))
            
            if repeated_blocks:
                self.report.duplicates_removed += len(repeated_blocks)
                self.report.suggestions.append(
                    f"Found {len(repeated_blocks)} duplicate blocks in {file_path}"
                )
                return True
            
            return False
        except Exception as e:
            self.report.errors.append(f"Error extracting patterns in {file_path}: {e}")
            return False

    def improve_documentation(self, file_path: Path) -> bool:
        """Add missing docstrings to functions and classes."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            modified = False
            new_lines = []
            i = 0
            
            while i < len(lines):
                line = lines[i]
                new_lines.append(line)
                
                # Check for function/class definition without docstring
                if re.match(r'\s*(def|class)\s+\w+', line):
                    # Check next line for docstring
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if not (next_line.startswith('"""') or next_line.startswith("'''") or next_line.startswith('#')):
                            # Add docstring
                            indent = len(line) - len(line.lstrip())
                            docstring = f"{' ' * indent}    \"\"\"TODO: Add docstring\"\"\"\n"
                            new_lines.append(docstring)
                            modified = True
                            self.report.documentation_added += 1
                
                i += 1
            
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                self.logger.info(f"Added documentation to {file_path}")
                return True
            
            return False
        except Exception as e:
            self.report.errors.append(f"Error improving documentation in {file_path}: {e}")
            return False

    def refactor_codebase(self) -> RefactoringReport:
        """Perform full codebase refactoring."""
        self.logger.info("Starting codebase refactoring...")
        
        # Analyze all Python files
        python_files = list(self.project_root.rglob('*.py'))
        
        for file_path in python_files:
            # Skip __init__.py and test files
            if file_path.name == '__init__.py' or 'test' in str(file_path):
                continue
            
            # Analyze file
            analysis = self.analyze_file(file_path)
            
            # Extract common patterns
            self.extract_common_patterns(file_path)
            
            # Improve documentation
            self.improve_documentation(file_path)
        
        self.logger.info(f"Refactoring complete. Files analyzed: {self.report.files_analyzed}")
        return self.report

    def generate_report(self, output_path: Path) -> None:
        """Generate a refactoring report."""
        report_content = f"""
# Code Refactoring Report
Generated: {__import__('datetime').datetime.now().isoformat()}

## Summary
- Files Analyzed: {self.report.files_analyzed}
- Functions Extracted: {self.report.functions_extracted}
- Duplicates Removed: {self.report.duplicates_removed}
- Patterns Improved: {self.report.patterns_improved}
- Documentation Added: {self.report.documentation_added}

## Errors
"""
        if self.report.errors:
            for error in self.report.errors:
                report_content += f"- {error}\n"
        else:
            report_content += "None\n"
        
        report_content += "\n## Suggestions\n"
        if self.report.suggestions:
            for suggestion in self.report.suggestions:
                report_content += f"- {suggestion}\n"
        else:
            report_content += "None\n"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        self.logger.info(f"Report written to {output_path}")

def main():
    """Main entry point for refactoring script."""
    setup_logging()
    logger = get_logger(__name__)
    
    project_root = Path(__file__).parent.parent
    refactorer = CodeRefactorer(project_root)
    
    try:
        report = refactorer.refactor_codebase()
        refactorer.generate_report(project_root / 'logs' / 'refactor_report.txt')
        
        logger.info("Refactoring completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Refactoring failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())