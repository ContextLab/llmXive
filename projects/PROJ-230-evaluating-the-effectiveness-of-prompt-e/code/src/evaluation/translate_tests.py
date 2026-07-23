"""
Translate Python unit tests to JavaScript using a deterministic AST-based transpiler.

This module strictly forbids LLM-based test generation (FR-003).
It uses 'transcrypt' as the deterministic transpiler for converting Python test files
to JavaScript, ensuring reproducible and verifiable test translations.

The transpiled tests will be used to evaluate the functional correctness of
LLM-generated JavaScript translations of Python code.
"""
import os
import sys
import subprocess
import logging
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Ensure transcrypt is available
try:
    import transcrypt
except ImportError:
    logger.error("transcrypt is not installed. Please install it with: pip install transcrypt")
    sys.exit(1)

def ensure_transcrypt_available() -> bool:
    """
    Verify that transcrypt is installed and available.
    
    Returns:
        bool: True if transcrypt is available, False otherwise.
    """
    try:
        import transcrypt
        logger.info(f"Transcrypt version: {transcrypt.__version__}")
        return True
    except ImportError:
        logger.error("Transcrypt is not installed. Cannot proceed with test translation.")
        return False

def translate_python_test_to_js(
    python_test_path: Path,
    output_js_path: Path,
    build_dir: Optional[Path] = None
) -> bool:
    """
    Translate a Python unit test file to JavaScript using transcrypt.
    
    Args:
        python_test_path: Path to the Python test file.
        output_js_path: Path where the translated JavaScript file should be saved.
        build_dir: Optional directory for transcrypt build artifacts.
        
    Returns:
        bool: True if translation was successful, False otherwise.
        
    Raises:
        RuntimeError: If transcrypt fails to translate the file.
    """
    if not python_test_path.exists():
        logger.error(f"Python test file not found: {python_test_path}")
        return False

    if not python_test_path.suffix == '.py':
        logger.error(f"Expected a .py file, got: {python_test_path.suffix}")
        return False

    # Create a temporary directory for transcrypt build if not provided
    if build_dir is None:
        build_dir = Path(tempfile.mkdtemp(prefix="transcrypt_build_"))
        logger.debug(f"Using temporary build directory: {build_dir}")
    else:
        build_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Run transcrypt to convert Python to JavaScript
        # Using command-line interface for better control
        cmd = [
            sys.executable, '-m', 'transcrypt',
            '-b',  # Build
            '-m',  # Minify (optional, can be removed for debugging)
            '-n',  # No license header
            '-k',  # Keep build directory
            '-o', str(build_dir),  # Output directory
            str(python_test_path)
        ]

        logger.info(f"Running transcrypt: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout for translation
        )

        if result.returncode != 0:
            logger.error(f"Transcrypt failed with return code {result.returncode}")
            logger.error(f"stdout: {result.stdout}")
            logger.error(f"stderr: {result.stderr}")
            return False

        # Find the generated JavaScript file
        # Transcrypt typically generates files in <build_dir>/__target__/
        target_dir = build_dir / '__target__'
        if not target_dir.exists():
            logger.error(f"Transcrypt target directory not found: {target_dir}")
            return False

        # Look for the generated JS file (same base name as input)
        base_name = python_test_path.stem
        js_files = list(target_dir.glob(f"{base_name}*.js"))
        
        if not js_files:
            logger.error(f"No JavaScript files generated for {base_name}")
            logger.error(f"Files in target directory: {list(target_dir.iterdir())}")
            return False

        # Use the first matching JS file
        generated_js = js_files[0]
        logger.debug(f"Generated JS file: {generated_js}")

        # Copy to the desired output path
        output_js_path.parent.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copy2(generated_js, output_js_path)
        
        logger.info(f"Successfully translated {python_test_path} to {output_js_path}")
        return True

    except subprocess.TimeoutExpired:
        logger.error(f"Transcrypt timed out while translating {python_test_path}")
        return False
    except Exception as e:
        logger.error(f"Error during translation of {python_test_path}: {str(e)}")
        return False

def translate_test_directory(
    input_dir: Path,
    output_dir: Path,
    recursive: bool = True
) -> Dict[str, Any]:
    """
    Translate all Python test files in a directory to JavaScript.
    
    Args:
        input_dir: Directory containing Python test files.
        output_dir: Directory where translated JavaScript files will be saved.
        recursive: Whether to search recursively for Python files.
        
    Returns:
        Dict containing translation statistics.
    """
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        return {'success': 0, 'failed': 0, 'total': 0}

    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all Python test files
    pattern = '**/*.py' if recursive else '*.py'
    python_files = list(input_dir.glob(pattern))
    
    # Filter for test files (files starting with 'test_' or ending with '_test.py')
    test_files = [
        f for f in python_files
        if f.name.startswith('test_') or f.name.endswith('_test.py')
    ]

    logger.info(f"Found {len(test_files)} Python test files to translate")

    stats = {'success': 0, 'failed': 0, 'total': len(test_files)}

    for py_file in test_files:
        # Compute relative path to preserve directory structure
        rel_path = py_file.relative_to(input_dir)
        js_file = output_dir / rel_path.with_suffix('.js')

        logger.info(f"Translating: {py_file} -> {js_file}")
        
        success = translate_python_test_to_js(py_file, js_file)
        
        if success:
            stats['success'] += 1
        else:
            stats['failed'] += 1
            logger.warning(f"Failed to translate: {py_file}")

    logger.info(f"Translation complete: {stats['success']}/{stats['total']} successful")
    return stats

def main():
    """
    Main entry point for the test translation script.
    
    This script translates Python unit tests to JavaScript using transcrypt,
    ensuring deterministic and reproducible test translations for evaluation.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Check if transcrypt is available
    if not ensure_transcrypt_available():
        sys.exit(1)

    # Default paths - these should be configured via command line args or config
    # For now, use project-standard paths
    input_dir = Path('data/raw/python_tests')
    output_dir = Path('data/processed/js_tests')

    # Check if input directory exists, if not, look for alternative locations
    if not input_dir.exists():
        # Try common alternative locations
        alternative_dirs = [
            Path('data/raw/tests'),
            Path('data/tests'),
            Path('tests')
        ]
        
        found = False
        for alt_dir in alternative_dirs:
            if alt_dir.exists() and any(alt_dir.glob('**/*.py')):
                input_dir = alt_dir
                logger.info(f"Using alternative input directory: {input_dir}")
                found = True
                break
        
        if not found:
            logger.error(f"No Python test files found in any expected directory")
            logger.error(f"Expected in: {input_dir}")
            logger.error("Please ensure Python test files are available for translation")
            sys.exit(1)

    logger.info(f"Translating Python tests from: {input_dir}")
    logger.info(f"Output directory: {output_dir}")

    # Perform translation
    stats = translate_test_directory(input_dir, output_dir)

    # Log final statistics
    logger.info("=" * 60)
    logger.info("TRANSLATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total files: {stats['total']}")
    logger.info(f"Successful: {stats['success']}")
    logger.info(f"Failed: {stats['failed']}")
    logger.info(f"Success rate: {stats['success']/stats['total']*100:.1f}%" if stats['total'] > 0 else "N/A")
    logger.info("=" * 60)

    # Exit with error code if all translations failed
    if stats['total'] > 0 and stats['success'] == 0:
        logger.error("All translations failed!")
        sys.exit(1)

    logger.info("Test translation completed successfully")

if __name__ == '__main__':
    main()
