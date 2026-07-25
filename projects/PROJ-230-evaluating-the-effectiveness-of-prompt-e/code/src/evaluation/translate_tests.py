"""
translate_tests.py

Converts Python unit tests to JavaScript using Transcrypt (a deterministic transpiler).
Strictly forbids LLM-based test generation (FR-003).
"""
import os
import sys
import subprocess
import logging
import tempfile
from pathlib import Path
from typing import Optional

# Ensure we can import from the project root if run as a module
try:
    from src.utils.logging import get_logger
except ImportError:
    # Fallback for direct execution in case src is not in path
    import logging
    def get_logger(name):
        return logging.getLogger(name)

logger = get_logger(__name__)

# Constants
TRANSCRYPT_CMD = "transcrypt"
TRANSCRYPT_MIN_VERSION = (3, 8, 0)  # Minimum expected version
DEFAULT_OUTPUT_DIR = "data/evaluation/translated_tests"
INPUT_TEST_DIR = "data/raw/tests"  # Assumed location for raw Python tests

def ensure_transcrypt_available() -> bool:
    """
    Checks if 'transcrypt' is installed and available in PATH.
    Installs it if missing (via pip).
    Returns True if available, False otherwise.
    """
    logger.info("Checking for Transcrypt availability...")
    try:
        result = subprocess.run(
            ["transcrypt", "-version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            logger.info(f"Transcrypt found: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        logger.warning("Transcrypt not found in PATH. Attempting installation via pip...")
    except subprocess.TimeoutExpired:
        logger.error("Transcrypt version check timed out.")
        return False
    except Exception as e:
        logger.error(f"Error checking Transcrypt: {e}")
        return False

    # Attempt installation
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "transcrypt", "-q"],
            check=True,
            timeout=60
        )
        logger.info("Transcrypt installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install Transcrypt: {e}")
        return False
    except subprocess.TimeoutExpired:
        logger.error("Transcrypt installation timed out.")
        return False

def translate_python_test_to_js(
    python_test_path: Path,
    output_dir: Path,
    preserve_structure: bool = True
) -> Optional[Path]:
    """
    Translates a single Python test file to JavaScript using Transcrypt.

    Args:
        python_test_path: Path to the input .py test file.
        output_dir: Directory where the compiled JS will be placed.
        preserve_structure: If True, maintains subdirectory structure relative to input.

    Returns:
        Path to the generated .js file, or None if translation failed.
    """
    if not python_test_path.exists():
        logger.error(f"Input file not found: {python_test_path}")
        return None

    if not python_test_path.suffix == ".py":
        logger.warning(f"Skipping non-Python file: {python_test_path}")
        return None

    logger.info(f"Translating: {python_test_path}")

    # Determine output path
    if preserve_structure:
        # Calculate relative path from a base (e.g., data/raw/tests)
        # We assume the caller passes the correct base context or we use the file's parent
        relative_path = python_test_path.relative_to(python_test_path.parent.parent)
        target_dir = output_dir / relative_path.parent
    else:
        target_dir = output_dir

    target_dir.mkdir(parents=True, exist_ok=True)
    output_js_path = target_dir / f"{python_test_path.stem}.js"

    # Transcrypt command construction
    # -m: no module
    # -a: generate annotations (optional but helpful for debugging)
    # -b: build only (no HTML)
    # -d: debug mode (optional)
    # We target the specific file to compile
    cmd = [
        TRANSCRYPT_CMD,
        "-b",       # Build only (no HTML)
        "-m",       # No module wrapper (standalone script)
        "-a",       # Add annotations
        "-d",       # Debug mode (helps with error reporting)
        "-n",       # No minification (easier to read/debug)
        "-k",       # Keep generated files in target
        str(python_test_path)
    ]

    try:
        # Run transcrypt. Note: Transcrypt often writes to a 'target' subdirectory
        # inside the source directory or the current working directory.
        # To control output, we might need to run it in a temp dir or parse its output.
        # However, standard usage is: transcrypt [options] <source>.
        # It creates a 'target' folder. We will move the result.

        # Strategy: Run transcrypt in the parent of the output dir to control placement,
        # or run in temp and move. Let's try running in a temp dir to avoid pollution.
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            # Copy source to tmp to run transcrypt there
            temp_src = tmp_path / python_test_path.name
            temp_src.write_text(python_test_path.read_text())

            # Run transcrypt in tmp_dir
            # We need to tell it where to put the 'target' folder or move it afterwards.
            # Transcrypt defaults to creating 'target' in the current working directory.
            proc = subprocess.run(
                cmd,
                cwd=tmp_dir,
                capture_output=True,
                text=True,
                timeout=30
            )

            if proc.returncode != 0:
                logger.error(f"Transcrypt failed for {python_test_path}: {proc.stderr}")
                # Check for specific errors (e.g., syntax errors in Python)
                if "SyntaxError" in proc.stderr:
                    logger.error("Syntax error in Python test file. Cannot translate.")
                return None

            # Transcrypt creates 'target' folder in cwd (tmp_dir)
            target_folder = tmp_path / "target"
            if not target_folder.exists():
                logger.error(f"Transcrypt did not create target folder in {tmp_dir}")
                return None

            # Find the generated .js file
            # It usually matches the source stem
            js_candidates = list(target_folder.glob(f"{python_test_path.stem}.js"))
            
            if not js_candidates:
                # Maybe it's in a subfolder if module structure was inferred?
                # Try recursive search
                js_candidates = list(target_folder.rglob(f"{python_test_path.stem}.js"))
            
            if not js_candidates:
                logger.error(f"Could not find generated JS for {python_test_path} in {target_folder}")
                return None

            js_file = js_candidates[0]

            # Move to final destination
            # Ensure output dir exists
            output_js_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Read and write to ensure permissions and atomicity
            content = js_file.read_text()
            output_js_path.write_text(content)

            logger.info(f"Successfully translated to: {output_js_path}")
            return output_js_path

    except subprocess.TimeoutExpired:
        logger.error(f"Transcrypt timed out for {python_test_path}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error translating {python_test_path}: {e}")
        return None

def translate_test_directory(
    input_dir: Path,
    output_dir: Path,
    recursive: bool = True
) -> int:
    """
    Translates all Python test files in a directory to JavaScript.

    Args:
        input_dir: Directory containing Python test files.
        output_dir: Directory to save translated JavaScript files.
        recursive: If True, search subdirectories.

    Returns:
        Number of successfully translated files.
    """
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        return 0

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    # Ensure Transcrypt is available
    if not ensure_transcrypt_available():
        logger.critical("Transcrypt not available. Aborting translation.")
        return 0

    # Find all .py files
    pattern = "**/*.py" if recursive else "*.py"
    py_files = list(input_dir.glob(pattern))

    if not py_files:
        logger.warning(f"No Python files found in {input_dir}")
        return 0

    logger.info(f"Found {len(py_files)} Python files to translate.")

    success_count = 0
    for py_file in py_files:
        # Skip __init__.py or other non-test files if necessary
        if py_file.name.startswith("__"):
            continue

        result = translate_python_test_to_js(py_file, output_dir, preserve_structure=True)
        if result:
            success_count += 1
        else:
            logger.warning(f"Failed to translate: {py_file}")

    logger.info(f"Translation complete. Successful: {success_count}/{len(py_files)}")
    return success_count

def main():
    """Main entry point for the test translation task."""
    # Default paths relative to project root
    # Adjust based on actual project structure if different
    input_path = Path("data/raw/tests")
    output_path = Path(DEFAULT_OUTPUT_DIR)

    # Allow override via command line
    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])

    logger.info(f"Starting test translation from {input_path} to {output_path}")
    
    count = translate_test_directory(input_path, output_path)
    
    if count == 0:
        logger.warning("No tests were translated. Check logs for errors.")
        sys.exit(1)
    else:
        logger.info(f"Successfully translated {count} test files.")
        sys.exit(0)

if __name__ == "__main__":
    # Setup basic logging for direct execution
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    main()
