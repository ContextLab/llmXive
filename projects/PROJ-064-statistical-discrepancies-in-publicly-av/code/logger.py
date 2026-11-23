import logging
import sys
import os
import json
import hashlib
import argparse
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

# Custom JSON Formatter for structured logging
class JSONFormatter(logging.Formatter):
    """
    A logging formatter that outputs JSON objects.
    Ensures keys 'checksum', 'artifact_hash', and 'reproducible_flag' are present
    when relevant context is available.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }

        # Inject reproducibility keys if present in extra context
        if hasattr(record, 'checksum'):
            log_entry['checksum'] = record.checksum
        if hasattr(record, 'artifact_hash'):
            log_entry['artifact_hash'] = record.artifact_hash
        if hasattr(record, 'reproducible_flag'):
            log_entry['reproducible_flag'] = record.reproducible_flag

        return json.dumps(log_entry)

class ReproducibilityContext:
    """
    Context manager to wrap logging calls with reproducibility metadata.
    """
    def __init__(self, logger: logging.Logger, artifact_path: Optional[str] = None):
        self.logger = logger
        self.artifact_path = artifact_path
        self.checksum: Optional[str] = None
        self.artifact_hash: Optional[str] = None
        self.reproducible_flag: bool = False

        if artifact_path and os.path.exists(artifact_path):
            self._compute_hashes(artifact_path)

    def _compute_hashes(self, path: str):
        """Compute SHA-256 hash of the file."""
        try:
            sha256_hash = hashlib.sha256()
            with open(path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            self.artifact_hash = sha256_hash.hexdigest()
            self.checksum = self.artifact_hash # Alias for clarity
            self.reproducible_flag = True
        except Exception as e:
            self.logger.warning(f"Failed to compute hash for {path}: {e}")
            self.reproducible_flag = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def log_with_hashes(self, level: int, message: str):
        """Log a message with the computed hashes attached."""
        extra = {
            'checksum': self.checksum,
            'artifact_hash': self.artifact_hash,
            'reproducible_flag': self.reproducible_flag
        }
        self.logger.log(level, message, extra=extra)

# Global logger instance
_logger_instance: Optional[logging.Logger] = None

def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Configures the root logger with a JSON formatter and optional file handler.
    """
    global _logger_instance
    if _logger_instance is not None:
        return _logger_instance

    logger = logging.getLogger("llmXive_project")
    logger.setLevel(level)
    logger.handlers = []  # Clear existing handlers

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)

    # File Handler (if specified)
    if log_file:
        # Ensure directory exists
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)

    _logger_instance = logger
    return logger

def get_logger(name: str = "llmXive_project") -> logging.Logger:
    """
    Retrieves or creates a logger with the specified name.
    """
    return logging.getLogger(name)

def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    artifact_path: Optional[str] = None
):
    """
    Logs a message with reproducibility context if an artifact path is provided.
    """
    if artifact_path:
        with ReproducibilityContext(logger, artifact_path) as ctx:
            ctx.log_with_hashes(level, message)
    else:
        logger.log(level, message)

def get_logger_for_module(module_name: str) -> logging.Logger:
    """
    Returns a logger specifically for a given module name.
    """
    return logging.getLogger(module_name)

def verify_reproducible(artifact_path: str) -> Dict[str, Any]:
    """
    Computes and returns the reproducibility metadata for a given artifact.
    Used for the --verify-reproducible flag.
    """
    if not os.path.exists(artifact_path):
        return {
            "status": "error",
            "message": f"Artifact not found: {artifact_path}"
        }

    try:
        sha256_hash = hashlib.sha256()
        with open(artifact_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        artifact_hash = sha256_hash.hexdigest()
        
        return {
            "status": "verified",
            "artifact_path": artifact_path,
            "checksum": artifact_hash,
            "artifact_hash": artifact_hash,
            "reproducible_flag": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "reproducible_flag": False
        }

def main():
    """
    CLI entry point for logging infrastructure and verification.
    Supports --verify-reproducible flag.
    """
    parser = argparse.ArgumentParser(
        description="Logging infrastructure for llmXive project."
    )
    parser.add_argument(
        "--verify-reproducible",
        type=str,
        metavar="PATH",
        help="Verify reproducibility of the artifact at PATH and print hashes."
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default="logs/project.log",
        help="Path to the log file (default: logs/project.log)."
    )
    parser.add_argument(
        "--level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level."
    )

    args = parser.parse_args()

    if args.verify_reproducible:
        result = verify_reproducible(args.verify_reproducible)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["status"] == "verified" else 1)

    # Standard logging setup if no verification requested
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR
    }
    logger = setup_logging(log_file=args.log_file, level=level_map.get(args.level, logging.INFO))
    
    # Demonstrate usage
    logger.info("Logger initialized successfully.")
    logger.info("JSON formatting active.")
    
    # Example of logging with context
    test_artifact = args.verify_reproducible # Intentionally reusing if passed, or None
    if not test_artifact:
        # Create a dummy file to demonstrate context logging if no path provided
        dummy_path = "data/processed/dummy_demo.txt"
        Path(dummy_path).parent.mkdir(parents=True, exist_ok=True)
        with open(dummy_path, "w") as f:
            f.write("Demo artifact for logging verification.")
        test_artifact = dummy_path
        logger.info(f"Created demo artifact at {test_artifact} for context logging.")

    log_with_context(logger, logging.INFO, "Processing artifact with context", artifact_path=test_artifact)
    logger.info("Logging demonstration complete.")

if __name__ == "__main__":
    main()
