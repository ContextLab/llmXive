"""
Validation script for quickstart.md.

This script verifies that the quickstart documentation exists, is readable,
and contains the expected sections and instructions based on the project
specification.
"""
import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.config import get_project_root, get_data_dir, get_processed_dir, ensure_directories


class QuickstartValidationError(Exception):
    """Custom exception for quickstart validation failures."""
    pass


def check_file_exists(file_path: Path) -> bool:
    """Check if a file exists and is readable."""
    if not file_path.exists():
        return False
    if not file_path.is_file():
        return False
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1)  # Try to read at least one character
        return True
    except Exception:
        return False


def load_quickstart_content(file_path: Path) -> str:
    """Load and return the content of quickstart.md."""
    if not check_file_exists(file_path):
        raise QuickstartValidationError(f"File not found or not readable: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def validate_required_sections(content: str, file_path: Path) -> List[str]:
    """
    Validate that the quickstart.md contains all required sections.
    
    Returns a list of missing sections.
    """
    required_sections = [
        r'#.*Quickstart',
        r'#.*Installation',
        r'#.*Data.*Requirements',
        r'#.*Usage',
        r'#.*Output',
        r'#.*Pipeline.*Overview'
    ]
    
    missing_sections = []
    for pattern in required_sections:
        if not re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
            # Extract a more readable section name from the pattern
            section_name = pattern.replace(r'#.*', '').replace(r'\s+', ' ').strip()
            if not section_name:
                section_name = pattern
            missing_sections.append(section_name)
    
    return missing_sections


def validate_code_snippets(content: str, file_path: Path) -> List[str]:
    """
    Validate that code snippets reference valid commands and paths.
    
    Returns a list of invalid references.
    """
    invalid_refs = []
    
    # Check for python command references
    python_commands = re.findall(r'```bash\s*python\s+([^\s`]+)', content, re.MULTILINE)
    for cmd in python_commands:
        # Normalize path (remove ./ if present)
        if cmd.startswith('./'):
            cmd = cmd[2:]
        
        # Check if the referenced file exists
        full_path = file_path.parent / cmd
        if not full_path.exists():
            invalid_refs.append(f"Code snippet references non-existent file: {cmd}")
    
    # Check for data path references
    data_paths = re.findall(r'data/processed/([^\s`\n]+)', content)
    for path in data_paths:
        full_path = get_project_root() / 'data' / 'processed' / path
        if not full_path.exists():
            # This is a warning, not necessarily an error if the file is generated later
            pass  # Skip for now, as output files may not exist yet
    
    return invalid_refs


def validate_environment_setup(content: str) -> bool:
    """
    Validate that the quickstart includes environment setup instructions.
    
    Returns True if environment setup is documented, False otherwise.
    """
    env_patterns = [
        r'virtualenv',
        r'venv',
        r'conda',
        r'pip\s+install',
        r'requirements\.txt'
    ]
    
    for pattern in env_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    
    return False


def validate_pipeline_steps(content: str) -> Tuple[bool, List[str]]:
    """
    Validate that the quickstart describes the main pipeline steps.
    
    Returns (is_valid, list of missing steps).
    """
    expected_steps = [
        r'acquisition',
        r'preprocessing',
        r'modeling',
        r'robustness'
    ]
    
    missing_steps = []
    for step in expected_steps:
        if not re.search(step, content, re.IGNORECASE):
            missing_steps.append(step)
    
    return len(missing_steps) == 0, missing_steps


def validate_quickstart(file_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Perform comprehensive validation of quickstart.md.
    
    Args:
        file_path: Optional path to quickstart.md. If not provided, 
                  looks in specs/001-gene-regulation/quickstart.md
    
    Returns:
        Dictionary with validation results:
        {
            'success': bool,
            'errors': List[str],
            'warnings': List[str],
            'content_length': int,
            'sections_found': List[str],
            'code_snippets_valid': bool
        }
    """
    if file_path is None:
        # Default location based on project structure
        file_path = get_project_root() / 'specs' / '001-gene-regulation' / 'quickstart.md'
    
    result = {
        'success': True,
        'errors': [],
        'warnings': [],
        'content_length': 0,
        'sections_found': [],
        'code_snippets_valid': True,
        'file_path': str(file_path)
    }
    
    # Check file existence
    if not check_file_exists(file_path):
        result['success'] = False
        result['errors'].append(f"quickstart.md not found at expected location: {file_path}")
        return result
    
    # Load content
    try:
        content = load_quickstart_content(file_path)
        result['content_length'] = len(content)
    except QuickstartValidationError as e:
        result['success'] = False
        result['errors'].append(str(e))
        return result
    
    # Validate required sections
    missing_sections = validate_required_sections(content, file_path)
    if missing_sections:
        result['errors'].append(f"Missing required sections: {', '.join(missing_sections)}")
        result['success'] = False
    
    # Validate code snippets
    invalid_refs = validate_code_snippets(content, file_path)
    if invalid_refs:
        result['errors'].extend(invalid_refs)
        result['code_snippets_valid'] = False
        result['success'] = False
    
    # Validate environment setup
    if not validate_environment_setup(content):
        result['warnings'].append("Environment setup instructions not clearly documented")
    
    # Validate pipeline steps
    steps_valid, missing_steps = validate_pipeline_steps(content)
    if not steps_valid:
        result['warnings'].append(f"Missing pipeline step references: {', '.join(missing_steps)}")
    
    # Check for output file references
    output_files = [
        'data/processed/cleaned_dataset.csv',
        'data/processed/model_results.json',
        'data/processed/model_results_summary.csv',
        'data/processed/robustness_report.json'
    ]
    
    for output_file in output_files:
        if output_file not in content:
            result['warnings'].append(f"Output file not referenced in quickstart: {output_file}")
    
    return result


def main() -> int:
    """
    Main entry point for quickstart validation.
    
    Returns:
        0 if validation passes, 1 if validation fails
    """
    print("Starting quickstart.md validation...")
    
    # Allow optional path override via command line
    file_path = None
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
        print(f"Validating custom path: {file_path}")
    
    try:
        validation_result = validate_quickstart(file_path)
        
        print(f"\nValidation Results for: {validation_result['file_path']}")
        print(f"Content Length: {validation_result['content_length']} characters")
        print(f"Overall Status: {'PASSED' if validation_result['success'] else 'FAILED'}")
        
        if validation_result['errors']:
            print("\nErrors:")
            for error in validation_result['errors']:
                print(f"  - {error}")
        
        if validation_result['warnings']:
            print("\nWarnings:")
            for warning in validation_result['warnings']:
                print(f"  - {warning}")
        
        if validation_result['success']:
            print("\n✓ Quickstart validation PASSED")
            return 0
        else:
            print("\n✗ Quickstart validation FAILED")
            return 1
            
    except Exception as e:
        print(f"\n✗ Unexpected error during validation: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())