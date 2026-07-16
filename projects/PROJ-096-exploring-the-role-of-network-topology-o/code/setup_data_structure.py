"""
Data directory structure setup and metadata schema initialization.

This module ensures the required data directories exist and initializes
the checksums tracking file with the metadata schema.
"""
import os
import json
from pathlib import Path
import logging

# Configure logging for this module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root is assumed to be the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directories to ensure exist
REQUIRED_DIRS = [
    PROJECT_ROOT / 'data' / 'processed',
    PROJECT_ROOT / 'data' / 'checksums',
    PROJECT_ROOT / 'state' / 'projects',
]

CHECKSUMS_FILE = PROJECT_ROOT / 'data' / 'checksums.txt'

# Metadata schema definition
METADATA_SCHEMA = {
    "version": "1.0.0",
    "description": "Schema for tracking data artifacts in the research pipeline",
    "fields": [
        {
            "name": "file_path",
            "type": "string",
            "description": "Relative path to the file from project root",
            "required": True
        },
        {
            "name": "checksum",
            "type": "string",
            "description": "SHA-256 checksum of the file content",
            "required": True
        },
        {
            "name": "created_at",
            "type": "string",
            "description": "ISO 8601 timestamp of file creation",
            "required": True
        },
        {
            "name": "source_task",
            "type": "string",
            "description": "Task ID that generated this artifact",
            "required": False
        },
        {
            "name": "metadata",
            "type": "object",
            "description": "Additional metadata specific to the artifact type",
            "required": False
        }
    ],
    "supported_artifacts": [
        {
            "type": "graph",
            "extension": ".gpickle",
            "metadata_fields": ["nodes", "edges", "rewiring_prob", "seed"]
        },
        {
            "type": "simulation_result",
            "extension": ".csv",
            "metadata_fields": ["critical_coupling", "time_steps", "runtime"]
        },
        {
            "type": "analysis_report",
            "extension": ".md",
            "metadata_fields": ["correlation", "p_value", "methodology"]
        }
    ]
}

def ensure_directory(dir_path: Path) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        dir_path: Path to the directory to create
        
    Returns:
        True if directory exists or was created successfully, False otherwise
    """
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory ensured: {dir_path}")
        return True
    except OSError as e:
        logger.error(f"Failed to create directory {dir_path}: {e}")
        return False

def initialize_checksums_file() -> bool:
    """
    Initialize the checksums file with the metadata schema header.
    
    The file uses a tab-separated format for easy parsing:
    file_path\tchecksum\tcreated_at\tsource_task\tmetadata
    
    Returns:
        True if file was initialized successfully, False otherwise
    """
    try:
        # Create the file with header information
        with open(CHECKSUMS_FILE, 'w', encoding='utf-8') as f:
            # Write schema version and description as comments
            f.write(f"# Metadata Schema Version: {METADATA_SCHEMA['version']}\n")
            f.write(f"# Description: {METADATA_SCHEMA['description']}\n")
            f.write(f"# Generated: {Path(__file__).resolve()}\n")
            f.write("\n")
            
            # Write header row
            f.write("file_path\tchecksum\tcreated_at\tsource_task\tmetadata\n")
            
            # Write schema definition as JSON for reference
            f.write(f"# SCHEMA: {json.dumps(METADATA_SCHEMA, indent=2)}\n")
        
        logger.info(f"Checksums file initialized: {CHECKSUMS_FILE}")
        return True
    except OSError as e:
        logger.error(f"Failed to initialize checksums file {CHECKSUMS_FILE}: {e}")
        return False

def main() -> int:
    """
    Main entry point for data structure setup.
    
    Returns:
        0 on success, 1 on failure
    """
    logger.info("Starting data directory structure setup...")
    
    success = True
    
    # Ensure all required directories exist
    for dir_path in REQUIRED_DIRS:
        if not ensure_directory(dir_path):
            success = False
    
    # Initialize checksums file
    if not initialize_checksums_file():
        success = False
    
    if success:
        logger.info("Data directory structure setup completed successfully.")
        return 0
    else:
        logger.error("Data directory structure setup failed.")
        return 1

if __name__ == "__main__":
    exit(main())
