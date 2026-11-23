import os
import sys
import json
import argparse
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_java_compiler_path() -> Path:
    """
    Locate the javac compiler.
    Checks JAVA_HOME or falls back to system path.
    """
    java_home = os.environ.get('JAVA_HOME')
    if java_home:
        javac = Path(java_home) / 'bin' / 'javac'
        if javac.exists():
            return javac
    
    # Try system javac
    try:
        subprocess.run(['javac', '-version'], capture_output=True, check=True)
        return Path('javac')
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise RuntimeError(
            "javac not found. Please set JAVA_HOME or install JDK in PATH."
        )

def get_jar_name() -> str:
    """Returns the expected JAR filename."""
    return "halstead_calc.jar"

def build_halstead_jar(source_dir: Path) -> Path:
    """
    Compiles halstead_calc.java into halstead_calc.jar.
    Returns the path to the compiled JAR.
    """
    java_file = source_dir / "halstead_calc.java"
    jar_file = source_dir / get_jar_name()

    if not java_file.exists():
        raise FileNotFoundError(f"Source file not found: {java_file}")

    javac = get_java_compiler_path()
    
    logger.info(f"Compiling {java_file} to {jar_file}...")
    
    # Compile to class file first
    compile_cmd = [
        str(javac),
        "-d", str(source_dir),
        str(java_file)
    ]
    
    try:
        subprocess.run(compile_cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Compilation failed: {e.stderr}")
        raise RuntimeError(f"Failed to compile Java source: {e.stderr}")

    # Create JAR
    jar_cmd = [
        "jar", "cvf", str(jar_file),
        "-C", str(source_dir), "HalsteadCalc.class"
    ]
    
    try:
        subprocess.run(jar_cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"JAR creation failed: {e.stderr}")
        raise RuntimeError(f"Failed to create JAR: {e.stderr}")

    return jar_file

def load_file_list(file_list_path: Path) -> List[str]:
    """
    Loads a list of file paths from a JSON or text file.
    Expected format: JSON list of strings or newline-separated paths.
    """
    if not file_list_path.exists():
        raise FileNotFoundError(f"File list not found: {file_list_path}")

    with open(file_list_path, 'r') as f:
        content = f.read().strip()

    # Try JSON first
    if content.startswith('['):
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

    # Fallback to newline-separated
    return [line.strip() for line in content.splitlines() if line.strip()]

def calculate_halstead_single_file(java_file: Path, jar_path: Path) -> Optional[Dict[str, Any]]:
    """
    Runs the Halstead calculator JAR on a single Java file.
    Returns a dict with metrics or None if the file fails to parse.
    """
    if not java_file.exists():
        logger.warning(f"File not found, skipping: {java_file}")
        return None

    # Run the JAR
    cmd = [
        "java", "-jar", str(jar_path), str(java_file)
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30  # Timeout for large files
        )
        
        if result.returncode != 0:
            # Parse error or syntax error - log and skip
            error_msg = result.stderr.strip() or result.stdout.strip()
            if "Error" in error_msg or "Exception" in error_msg:
                logger.debug(f"Parse error in {java_file.name}: {error_msg[:100]}")
                return None
            else:
                # Unexpected error
                raise RuntimeError(f"Calculation failed for {java_file}: {result.stderr}")

        # Parse output
        # Expected output format: "operators: N1, operands: N2, volume: V, ..."
        # Or a JSON string if the Java code was updated to output JSON
        output = result.stdout.strip()
        
        # Try JSON parsing first
        try:
            metrics = json.loads(output)
            return metrics
        except json.JSONDecodeError:
            pass

        # Fallback to line parsing (assuming simple key: value format)
        metrics = {}
        for line in output.splitlines():
            if ':' in line:
                key, val = line.split(':', 1)
                key = key.strip()
                val = val.strip()
                try:
                    metrics[key] = float(val)
                except ValueError:
                    metrics[key] = val
        
        # Normalize keys to expected format if necessary
        if 'volume' in metrics:
            metrics['halstead_volume'] = metrics.pop('volume')
        
        return metrics if metrics else None

    except subprocess.TimeoutExpired:
        logger.warning(f"Timeout processing {java_file}")
        return None
    except Exception as e:
        logger.error(f"Error processing {java_file}: {e}")
        return None

def save_results(results: List[Dict[str, Any]], output_path: Path):
    """Saves the results to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")

def calculate_halstead_batch(
    file_list_path: Path,
    output_path: Path,
    source_dir: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Main entry point for batch processing.
    1. Ensures the JAR is built.
    2. Loads file list.
    3. Processes each file.
    4. Saves results.
    """
    # Determine source directory (default to script location)
    if source_dir is None:
        source_dir = Path(__file__).parent / "src" / "metrics"
    
    jar_path = build_halstead_jar(source_dir)
    
    file_paths = load_file_list(file_list_path)
    results = []
    
    logger.info(f"Processing {len(file_paths)} files...")
    
    for file_str in file_paths:
        file_path = Path(file_str)
        metrics = calculate_halstead_single_file(file_path, jar_path)
        
        if metrics is not None:
            metrics['file_path'] = str(file_path)
            results.append(metrics)
    
    save_results(results, output_path)
    return results

def main():
    parser = argparse.ArgumentParser(description="Wrapper for Halstead Volume Calculator")
    parser.add_argument(
        "--input", "-i",
        type=Path,
        required=True,
        help="Path to JSON or text file containing list of Java files"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        required=True,
        help="Path to output JSON results file"
    )
    parser.add_argument(
        "--source-dir", "-s",
        type=Path,
        default=None,
        help="Directory containing halstead_calc.java (default: code/src/metrics)"
    )
    
    args = parser.parse_args()
    
    try:
        calculate_halstead_batch(args.input, args.output, args.source_dir)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
