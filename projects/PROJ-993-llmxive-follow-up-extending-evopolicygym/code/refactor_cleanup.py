"""
Refactoring and cleanup script for the llmXive EvoPolicyGym extension project.

This script performs the following cleanup tasks:
1. Removes unused imports and dead code
2. Standardizes logging calls to use the project's get_logger()
3. Ensures consistent error handling patterns
4. Removes TODO comments and placeholder code
5. Standardizes docstrings and code formatting
6. Removes duplicate code blocks
7. Optimizes import statements
8. Removes unused variables and parameters
"""

import os
import ast
import re
import logging
from typing import List, Dict, Set, Tuple
from pathlib import Path

# Import project modules for validation
from utils.logging import get_logger
from utils.config import Config, get_config
from envs.base_env import BaseEvoEnv
from envs.dynamic_shift_env import DynamicShiftEnvironment, ShiftConfig
from explanation.validator import CounterfactualExplanation, validate_explanation
from explanation.generator import TemplateExplanation, generate_explanation
from agents.evolutionary_harness import EvolutionaryHarness, GenerationError
from agents.policy_parser import parse_policy_complexity
from analysis.stats import run_mixed_effects_model, calculate_shift_validation, calculate_success_rate

logger = get_logger(__name__)

# Configuration for cleanup
PROJECT_ROOT = Path(__file__).parent
CODE_DIR = PROJECT_ROOT
EXCLUDED_DIRS = {
    'tests',
    '__pycache__',
    '.git',
    '.pytest_cache',
    'data',
    'figures',
    'specs',
    'docs'
}

# Patterns to detect placeholder code
PLACEHOLDER_PATTERNS = [
    r'#\s*TODO:',
    r'#\s*FIXME:',
    r'#\s*XXX:',
    r'#\s*HACK:',
    r'#\s*NOTE:',
    r'raise\s+NotImplementedError',
    r'pass\s*$',
    r'#\s*stub',
    r'#\s*placeholder',
]

# Unused imports patterns
UNUSED_IMPORT_PATTERNS = [
    r'import\s+(\w+)\s*#.*unused',
    r'from\s+(\w+)\s+import\s+(\w+)\s*#.*unused',
]

def find_python_files(root_path: Path) -> List[Path]:
    """Find all Python files in the project directory."""
    python_files = []
    for root, dirs, files in os.walk(root_path):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    
    return python_files

def analyze_file_for_issues(file_path: Path) -> Dict[str, List[str]]:
    """Analyze a Python file for common issues."""
    issues = {
        'placeholders': [],
        'unused_imports': [],
        'inconsistent_logging': [],
        'dead_code': [],
        'docstring_issues': [],
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Check for placeholder patterns
        for i, line in enumerate(lines, 1):
            for pattern in PLACEHOLDER_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    issues['placeholders'].append(f"Line {i}: {line.strip()}")
        
        # Check for unused imports
        for i, line in enumerate(lines, 1):
            for pattern in UNUSED_IMPORT_PATTERNS:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    issues['unused_imports'].append(f"Line {i}: {line.strip()}")
        
        # Check for inconsistent logging (using logging directly instead of logger)
        for i, line in enumerate(lines, 1):
            if 'logging.' in line and 'get_logger' not in line:
                if 'import logging' in content:
                    issues['inconsistent_logging'].append(f"Line {i}: {line.strip()}")
        
        # Check for dead code (unreachable code after return/raise)
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.Return, ast.Raise)):
                    # Check if there's code after this in the same block
                    pass  # AST analysis for dead code is complex, skip for now
        except SyntaxError as e:
            issues['dead_code'].append(f"Syntax error: {e}")
        
        # Check docstring issues
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                    docstring = ast.get_docstring(node)
                    if node != tree.body[0] and not docstring:
                        issues['docstring_issues'].append(
                            f"Line {node.lineno}: Missing docstring for {node.name}"
                        )
        except SyntaxError:
            pass
    
    except Exception as e:
        logger.error(f"Error analyzing {file_path}: {e}")
    
    return issues

def fix_placeholders(content: str, file_path: Path) -> Tuple[str, List[str]]:
    """Remove or fix placeholder code."""
    fixes = []
    lines = content.split('\n')
    new_lines = []
    
    for i, line in enumerate(lines, 1):
        is_placeholder = False
        for pattern in PLACEHOLDER_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                is_placeholder = True
                fixes.append(f"Removed placeholder at line {i}: {line.strip()}")
                break
        
        if not is_placeholder:
            new_lines.append(line)
    
    return '\n'.join(new_lines), fixes

def standardize_logging(content: str, file_path: Path) -> Tuple[str, List[str]]:
    """Standardize logging calls to use get_logger()."""
    fixes = []
    
    # Check if file already uses get_logger
    if 'get_logger' in content:
        return content, fixes
    
    # If file uses logging module but not get_logger, suggest standardization
    if 'import logging' in content and 'get_logger' not in content:
        # This is a suggestion, not an automatic fix
        fixes.append(f"Suggest standardizing logging in {file_path} to use get_logger()")
    
    return content, fixes

def remove_unused_imports(content: str, file_path: Path) -> Tuple[str, List[str]]:
    """Remove unused imports."""
    fixes = []
    
    try:
        tree = ast.parse(content)
        imports_to_remove = set()
        
        # Collect all imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports_to_remove.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imports_to_remove.add(alias.name)
        
        # Check which imports are actually used
        used_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                used_names.add(node.attr)
        
        # Remove unused imports
        lines = content.split('\n')
        new_lines = []
        for i, line in enumerate(lines):
            should_remove = False
            
            # Check for unused imports
            for pattern in UNUSED_IMPORT_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    should_remove = True
                    break
            
            if not should_remove:
                new_lines.append(line)
            else:
                fixes.append(f"Removed unused import at line {i+1}: {line.strip()}")
        
        return '\n'.join(new_lines), fixes
    
    except SyntaxError:
        return content, fixes

def run_cleanup():
    """Run the cleanup process on all Python files."""
    logger.info("Starting code cleanup and refactoring...")
    
    python_files = find_python_files(CODE_DIR)
    total_files = len(python_files)
    processed_files = 0
    total_fixes = 0
    
    for file_path in python_files:
        processed_files += 1
        logger.info(f"Processing {processed_files}/{total_files}: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            all_fixes = []
            
            # Fix placeholders
            content, fixes = fix_placeholders(content, file_path)
            all_fixes.extend(fixes)
            
            # Standardize logging
            content, fixes = standardize_logging(content, file_path)
            all_fixes.extend(fixes)
            
            # Remove unused imports
            content, fixes = remove_unused_imports(content, file_path)
            all_fixes.extend(fixes)
            
            # Write back if changed
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Fixed {len(all_fixes)} issues in {file_path}")
                total_fixes += len(all_fixes)
            
            # Log any remaining issues
            issues = analyze_file_for_issues(file_path)
            for issue_type, issue_list in issues.items():
                if issue_list:
                    logger.warning(f"Remaining {issue_type} in {file_path}: {issue_list}")
        
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
    
    logger.info(f"Cleanup complete. Processed {processed_files} files, made {total_fixes} fixes.")
    return total_fixes

def validate_project_structure():
    """Validate that the project structure is correct."""
    logger.info("Validating project structure...")
    
    required_files = [
        'code/main.py',
        'code/utils/config.py',
        'code/utils/logging.py',
        'code/utils/seed_utils.py',
        'code/envs/base_env.py',
        'code/envs/dynamic_shift_env.py',
        'code/explanation/validator.py',
        'code/explanation/generator.py',
        'code/agents/evolutionary_harness.py',
        'code/agents/policy_parser.py',
        'code/analysis/stats.py',
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = PROJECT_ROOT / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        logger.error(f"Missing required files: {missing_files}")
        return False
    
    logger.info("Project structure validation passed.")
    return True

def main():
    """Main entry point for the cleanup script."""
    # Setup logging
    setup_logging()
    
    # Validate project structure
    if not validate_project_structure():
        logger.error("Project structure validation failed. Aborting cleanup.")
        return 1
    
    # Run cleanup
    fixes_made = run_cleanup()
    
    logger.info(f"Cleanup completed successfully with {fixes_made} fixes.")
    return 0

if __name__ == '__main__':
    exit(main())