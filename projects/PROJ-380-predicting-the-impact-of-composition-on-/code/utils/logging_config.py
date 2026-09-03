import logging
import sys
from pathlib import Path
from typing import Optional

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Gets or creates a logger with the specified name and level.
    Configures a handler if none exists.
    
    Args:
        name: Name of the logger.
        level: Logging level.
        
    Returns:
        Configured Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

def configure_root_logger(level: int = logging.INFO) -> None:
    """
    Configures the root logger.
    
    Args:
        level: Logging level for the root logger.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

def main():
    """CLI entry point for logging configuration."""
    import argparse
    parser = argparse.ArgumentParser(description="Logging Configuration")
    parser.add_argument("--level", type=str, default="INFO", 
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Logging level")
    args = parser.parse_args()

    level = getattr(logging, args.level.upper())
    configure_root_logger(level)
    logger = get_logger(__name__)
    logger.info(f"Root logger configured with level {args.level}")

if __name__ == "__main__":
    main()
