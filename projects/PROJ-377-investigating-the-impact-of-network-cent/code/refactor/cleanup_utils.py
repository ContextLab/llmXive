"""
Cleanup and Refactoring Utilities for llmXive Pipeline.

This module provides utilities for code cleanup, refactoring, and
environment validation to ensure the pipeline remains maintainable
and efficient.
"""
import os
import sys
import logging
import time
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import json
import glob

# Import existing logging utilities
from utils.logging import setup_logger

# Define base paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CODE_DIR = PROJECT_ROOT / "code"
TEMP_DIRS = [
    PROJECT_ROOT / "tmp",
    PROJECT_ROOT / "temp",
    PROJECT_ROOT / ".tmp",
    Path(tempfile.gettempdir()) / "llmxive",
]

def ensure_output_directories() -> Dict[str, bool]:
    """
    Ensure all required output directories exist.

    Returns:
        Dict mapping directory path to success status.
    """
    required_dirs = [
        DATA_DIR / "raw",
        DATA_DIR / "processed" / "behavioral",
        DATA_DIR / "processed" / "centrality",
        DATA_DIR / "processed" / "regression",
        DATA_DIR / "processed" / "validation",
        DATA_DIR / "processed" / "logs",
        DATA_DIR / "artifacts",
        CODE_DIR / "analysis",
        CODE_DIR / "data",
        CODE_DIR / "utils",
        CODE_DIR / "refactor",
    ]

    results = {}
    for dir_path in required_dirs:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            results[str(dir_path)] = True
        except Exception as e:
            results[str(dir_path)] = False
            logging.error(f"Failed to create directory {dir_path}: {e}")

    return results

def validate_environment() -> Tuple[bool, List[str]]:
    """
    Validate that the environment is properly configured.

    Checks:
    - Python version compatibility
    - Required directories exist
    - Required packages are importable

    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []

    # Check Python version
    if sys.version_info < (3, 8):
        issues.append(f"Python version {sys.version_info} is too old. Requires 3.8+")

    # Check required directories
    required_dirs = [DATA_DIR, CODE_DIR]
    for dir_path in required_dirs:
        if not dir_path.exists():
            issues.append(f"Required directory missing: {dir_path}")

    # Check required packages
    required_packages = [
        "pandas",
        "numpy",
        "networkx",
        "scikit-learn",
        "statsmodels",
        "nilearn",
        "matplotlib",
        "seaborn",
    ]

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            issues.append(f"Required package missing: {package}")

    return len(issues) == 0, issues

def cleanup_temp_files() -> Tuple[int, List[str]]:
    """
    Clean up temporary files and directories.

    Returns:
        Tuple of (number_of_files_removed, list_of_removed_paths)
    """
    removed_count = 0
    removed_paths = []

    for temp_dir in TEMP_DIRS:
        if temp_dir.exists():
            try:
                # Find all files
                files = list(temp_dir.glob("**/*"))
                for file_path in files:
                    if file_path.is_file():
                        try:
                            file_path.unlink()
                            removed_count += 1
                            removed_paths.append(str(file_path))
                        except Exception as e:
                            logging.warning(f"Failed to remove {file_path}: {e}")

                # Remove empty directories
                for dir_path in sorted(temp_dir.glob("**/*"), reverse=True):
                    if dir_path.is_dir():
                        try:
                            dir_path.rmdir()
                        except OSError:
                            pass  # Directory not empty

                # Remove the temp dir itself if empty
                try:
                    temp_dir.rmdir()
                except OSError:
                    pass

            except Exception as e:
                logging.error(f"Failed to clean temp directory {temp_dir}: {e}")

    return removed_count, removed_paths

def setup_pipeline_logger(log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up a logger for pipeline operations.

    Args:
        log_file: Optional path to log file. If None, logs to console only.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("llmxive_pipeline")
    logger.setLevel(logging.INFO)

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger

def log_pipeline_start(logger: logging.Logger, config: Optional[Dict[str, Any]] = None) -> None:
    """
    Log the start of a pipeline execution.

    Args:
        logger: Logger instance to use.
        config: Optional configuration dictionary to log.
    """
    logger.info("=" * 80)
    logger.info("Pipeline execution started")
    logger.info(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Python version: {sys.version}")

    if config:
        logger.info("Configuration:")
        for key, value in config.items():
            logger.info(f"  {key}: {value}")

    logger.info("=" * 80)

def log_pipeline_end(
    logger: logging.Logger, success: bool, duration: float, stats: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log the end of a pipeline execution.

    Args:
        logger: Logger instance to use.
        success: Whether the pipeline completed successfully.
        duration: Total execution time in seconds.
        stats: Optional statistics dictionary.
    """
    logger.info("=" * 80)
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"Pipeline execution {status}")
    logger.info(f"Duration: {duration:.2f} seconds")

    if stats:
        logger.info("Statistics:")
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")

    logger.info("=" * 80)

def validate_config_consistency(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that configuration values are consistent.

    Args:
        config: Configuration dictionary to validate.

    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []

    # Check for required keys
    required_keys = ["data_dir", "output_dir"]
    for key in required_keys:
        if key not in config:
            issues.append(f"Missing required configuration key: {key}")

    # Check path validity
    if "data_dir" in config:
        if not Path(config["data_dir"]).is_absolute():
            issues.append("data_dir should be an absolute path")

    # Check numeric constraints
    if "retention_threshold" in config:
        if not (0 <= config["retention_threshold"] <= 1):
            issues.append("retention_threshold must be between 0 and 1")

    if "power_threshold_n" in config:
        if config["power_threshold_n"] < 1:
            issues.append("power_threshold_n must be positive")

    return len(issues) == 0, issues

def merge_config_overrides(base_config: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge configuration overrides into base configuration.

    Args:
        base_config: Base configuration dictionary.
        overrides: Override values (nested dicts are merged recursively).

    Returns:
        Merged configuration dictionary.
    """
    result = base_config.copy()

    for key, value in overrides.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_config_overrides(result[key], value)
        else:
            result[key] = value

    return result

def generate_config_report(config: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Generate a human-readable configuration report.

    Args:
        config: Configuration dictionary.
        output_path: Optional path to save the report.

    Returns:
        The report as a string.
    """
    lines = ["Configuration Report", "=" * 40, ""]

    def format_dict(d: Dict[str, Any], indent: int = 0) -> List[str]:
        result = []
        prefix = "  " * indent
        for key, value in sorted(d.items()):
            if isinstance(value, dict):
                result.append(f"{prefix}{key}:")
                result.extend(format_dict(value, indent + 1))
            else:
                result.append(f"{prefix}{key}: {value}")
        return result

    lines.extend(format_dict(config))
    report = "\n".join(lines)

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(report)

    return report

def run_cleanup(
    logger: Optional[logging.Logger] = None,
    cleanup_temp: bool = True,
    validate_dirs: bool = True,
    output_report: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run the full cleanup and validation process.

    Args:
        logger: Optional logger instance.
        cleanup_temp: Whether to clean temporary files.
        validate_dirs: Whether to validate/create output directories.
        output_report: Optional path to save a cleanup report.

    Returns:
        Dictionary with cleanup results.
    """
    if logger is None:
        logger = setup_pipeline_logger()

    start_time = time.time()
    results = {
        "success": True,
        "errors": [],
        "warnings": [],
        "actions_taken": [],
    }

    logger.info("Starting cleanup and validation process...")

    # Validate environment
    is_valid, issues = validate_environment()
    if not is_valid:
        results["errors"].extend(issues)
        results["success"] = False
        for issue in issues:
            logger.error(f"Environment issue: {issue}")

    # Ensure directories
    if validate_dirs:
        dir_results = ensure_output_directories()
        for dir_path, success in dir_results.items():
            if success:
                results["actions_taken"].append(f"Ensured directory: {dir_path}")
            else:
                results["errors"].append(f"Failed to create directory: {dir_path}")
                results["success"] = False

    # Cleanup temp files
    if cleanup_temp:
        removed_count, removed_paths = cleanup_temp_files()
        results["actions_taken"].append(f"Removed {removed_count} temporary files")
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} temporary files")

    # Generate report
    if output_report:
        config = {
            "cleanup_temp": cleanup_temp,
            "validate_dirs": validate_dirs,
            "directories_ensured": list(ensure_output_directories().keys()),
            "temp_files_removed": removed_count if cleanup_temp else 0,
        }
        report = generate_config_report(config, output_report)
        results["actions_taken"].append(f"Generated report at {output_report}")
        logger.info(f"Cleanup report saved to {output_report}")

    duration = time.time() - start_time
    results["duration_seconds"] = duration

    logger.info(f"Cleanup process completed in {duration:.2f} seconds")
    if results["success"]:
        logger.info("Cleanup completed successfully")
    else:
        logger.error(f"Cleanup completed with {len(results['errors'])} errors")

    return results

def main() -> None:
    """Main entry point for cleanup script."""
    import argparse

    parser = argparse.ArgumentParser(description="Run cleanup and validation for llmXive pipeline")
    parser.add_argument("--log-file", type=str, help="Path to log file")
    parser.add_argument("--no-cleanup-temp", action="store_true", help="Skip temp file cleanup")
    parser.add_argument("--no-validate-dirs", action="store_true", help="Skip directory validation")
    parser.add_argument("--report", type=str, help="Path to save cleanup report")

    args = parser.parse_args()

    logger = setup_pipeline_logger(args.log_file)
    log_pipeline_start(logger)

    results = run_cleanup(
        logger=logger,
        cleanup_temp=not args.no_cleanup_temp,
        validate_dirs=not args.no_validate_dirs,
        output_report=args.report,
    )

    log_pipeline_end(
        logger,
        success=results["success"],
        duration=results["duration_seconds"],
        stats={
            "errors": len(results["errors"]),
            "warnings": len(results["warnings"]),
            "actions": len(results["actions_taken"]),
        },
    )

    sys.exit(0 if results["success"] else 1)

if __name__ == "__main__":
    main()
