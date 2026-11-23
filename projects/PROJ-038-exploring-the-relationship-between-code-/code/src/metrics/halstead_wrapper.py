"""
Wrapper script for Halstead Complexity Calculation.

This script builds the Java calculator (if needed), validates Java file syntax,
runs the calculator, and parses the output.

Usage: python code/src/metrics/halstead_wrapper.py <java_file_path>
Output: Prints a JSON object with Halstead metrics or an error.
"""
import os
import sys
import json
import subprocess
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Path constants
BASE_DIR = Path(__file__).parent
JAVA_FILE = BASE_DIR / "halstead_calc.java"
CLASS_FILE = BASE_DIR / "halstead_calc.class"
JAR_FILE = BASE_DIR / "halstead_calc.jar"

def get_java_compiler_path() -> str:
    """Get the path to the Java compiler (javac)."""
    # Try common locations or use system PATH
    possible_paths = [
        "javac",
        "/usr/bin/javac",
        "/usr/local/bin/javac",
        "/opt/java/bin/javac"
    ]
    
    for path in possible_paths:
        try:
            subprocess.run([path, "-version"], capture_output=True, check=True)
            return path
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    raise FileNotFoundError("Java compiler (javac) not found in system PATH or common locations.")

def build_halstead_jar() -> bool:
    """
    Compile the Java file into a JAR.
    
    Returns:
        bool: True if build successful, False otherwise.
    """
    if not JAVA_FILE.exists():
        logger.error(f"Java source file not found: {JAVA_FILE}")
        return False

    javac_path = get_java_compiler_path()
    
    try:
        # Compile to class file first
        logger.info(f"Compiling {JAVA_FILE}...")
        result = subprocess.run(
            [javac_path, str(JAVA_FILE)],
            capture_output=True,
            text=True,
            check=True
        )
        
        if result.stderr:
            logger.warning(f"Compilation warnings: {result.stderr}")
        
        # Create JAR (optional but good practice)
        logger.info(f"Creating JAR {JAR_FILE}...")
        subprocess.run(
            ["jar", "cf", str(JAR_FILE), "-C", str(BASE_DIR), "halstead_calc.class"],
            capture_output=True,
            check=True
        )
        
        logger.info("Build successful.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Compilation failed: {e.stderr}")
        return False
    except FileNotFoundError as e:
        logger.error(f"Tool not found: {e}")
        return False

def validate_java_syntax(file_path: Path) -> bool:
    """
    Validate that a Java file has valid syntax using javac.
    
    Args:
        file_path: Path to the Java file.
        
    Returns:
        bool: True if syntax is valid, False otherwise.
    """
    javac_path = get_java_compiler_path()
    
    try:
        # Try to compile the file (without generating output)
        result = subprocess.run(
            [javac_path, "-proc:none", "-Xlint:all", str(file_path)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.debug(f"Syntax validation failed for {file_path}: {result.stderr}")
            return False
        
        return True
    except subprocess.CalledProcessError as e:
        logger.debug(f"Syntax validation error for {file_path}: {e.stderr}")
        return False
    except FileNotFoundError as e:
        logger.error(f"Java compiler not found for validation: {e}")
        return False

def calculate_halstead_single_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Calculate Halstead metrics for a single Java file.
    
    Args:
        file_path: Path to the Java file.
        
    Returns:
        Dict with metrics or None if error.
    """
    # Ensure the JAR is built
    if not JAR_FILE.exists():
        if not build_halstead_jar():
            logger.error("Failed to build Halstead calculator JAR.")
            return None

    # Validate syntax first
    if not validate_java_syntax(file_path):
        logger.warning(f"Skipping {file_path}: Invalid Java syntax.")
        return None

    try:
        # Run the JAR
        result = subprocess.run(
            ["java", "-jar", str(JAR_FILE), str(file_path)],
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout per file
        )
        
        output = result.stdout.strip()
        
        if not output.startswith("HALSTEAD:"):
            logger.error(f"Unexpected output format for {file_path}: {output}")
            return None
        
        # Parse output: "HALSTEAD: volume=..., n1=..., ..."
        parts = output.split(": ", 1)
        if len(parts) != 2:
            logger.error(f"Failed to parse output for {file_path}: {output}")
            return None
        
        metrics_str = parts[1]
        metrics = {}
        
        for item in metrics_str.split(", "):
            if "=" in item:
                key, value = item.split("=", 1)
                key = key.strip()
                value = value.strip()
                
                if key == "ERROR":
                    logger.error(f"Java calculation error for {file_path}: {value}")
                    return None
                
                try:
                    metrics[key] = float(value)
                except ValueError:
                    metrics[key] = value
        
        metrics["file_path"] = str(file_path)
        return metrics
        
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout calculating Halstead for {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error calculating Halstead for {file_path}: {e}")
        return None

def calculate_halstead_batch(file_paths: list) -> list:
    """
    Calculate Halstead metrics for a list of Java files.
    
    Args:
        file_paths: List of Path objects to Java files.
        
    Returns:
        List of dictionaries with metrics.
    """
    results = []
    for file_path in file_paths:
        metrics = calculate_halstead_single_file(file_path)
        if metrics:
            results.append(metrics)
    return results

def main():
    parser = argparse.ArgumentParser(description="Calculate Halstead metrics for Java files.")
    parser.add_argument("file_path", type=Path, help="Path to the Java file.")
    parser.add_argument("--batch", nargs="+", type=Path, help="List of files for batch processing.")
    
    args = parser.parse_args()
    
    if args.batch:
        results = calculate_halstead_batch(args.batch)
        print(json.dumps(results, indent=2))
    elif args.file_path:
        metrics = calculate_halstead_single_file(args.file_path)
        if metrics:
            print(json.dumps(metrics, indent=2))
        else:
            print(json.dumps({"error": "Failed to calculate metrics"}))
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
