"""
Results export module for statistical analysis outputs.

Provides functions to export analysis results to CSV and JSON formats,
with validation for file size constraints.
"""

import os
import sys
import json
import csv
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict

# Add parent directory to path for imports
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from viz.logging import get_export_logger

# Configuration
MAX_EXPORT_FILE_SIZE = 14 * 1024 * 1024 * 1024  # 14 GB in bytes


@dataclass
class ExportResult:
    """Represents the result of an export operation."""
    success: bool
    file_path: str
    file_size_bytes: int
    message: str
    warnings: list


def export_to_csv(
    data: Union[Dict[str, Any], list],
    output_path: str,
    logger: Optional[logging.Logger] = None
) -> ExportResult:
    """
    Export analysis results to CSV format.
    
    Args:
        data: Data to export (dict of lists or list of dicts)
        output_path: Path where CSV file will be written
        logger: Logger instance for operation logging
    
    Returns:
        ExportResult containing success status and metadata
    """
    if logger is None:
        logger = get_export_logger()
    
    logger.info(f"Starting CSV export to {output_path}")
    
    try:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
        # Handle different data formats
        if isinstance(data, dict):
            # Convert dict of lists to list of dicts for CSV
            if all(isinstance(v, list) for v in data.values()):
                # Dict of lists -> list of dicts
                keys = list(data.keys())
                rows = [dict(zip(keys, vals)) for vals in zip(*data.values())]
            else:
                # Dict of single values -> single row
                rows = [data]
        elif isinstance(data, list):
            rows = data
        else:
            logger.error(f"Unsupported data type: {type(data)}")
            return ExportResult(
                success=False,
                file_path=str(output_path),
                file_size_bytes=0,
                message=f"Unsupported data type: {type(data)}",
                warnings=[]
            )
    
        # Write CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            else:
                # Write empty file with no rows
                f.write("")
    
        # Validate file size
        file_size = output_path.stat().st_size
        if file_size > MAX_EXPORT_FILE_SIZE:
            error_msg = f"Export file size ({file_size} bytes) exceeds limit ({MAX_EXPORT_FILE_SIZE} bytes)"
            logger.error(error_msg)
            # Remove the oversized file
            output_path.unlink()
            return ExportResult(
                success=False,
                file_path=str(output_path),
                file_size_bytes=file_size,
                message=error_msg,
                warnings=[]
            )
    
        logger.info(f"CSV export successful: {file_size} bytes")
        return ExportResult(
            success=True,
            file_path=str(output_path),
            file_size_bytes=file_size,
            message="CSV export completed successfully",
            warnings=[]
        )
    
    except Exception as e:
        logger.error(f"CSV export failed: {str(e)}")
        return ExportResult(
            success=False,
            file_path=str(output_path),
            file_size_bytes=0,
            message=f"CSV export failed: {str(e)}",
            warnings=[str(e)]
        )


def export_to_json(
    data: Dict[str, Any],
    output_path: str,
    metadata: Optional[Dict[str, Any]] = None,
    logger: Optional[logging.Logger] = None
) -> ExportResult:
    """
    Export analysis results to JSON format with optional metadata.
    
    Args:
        data: Data to export (dict structure)
        output_path: Path where JSON file will be written
        metadata: Optional metadata to include in the export
        logger: Logger instance for operation logging
    
    Returns:
        ExportResult containing success status and metadata
    """
    if logger is None:
        logger = get_export_logger()
    
    logger.info(f"Starting JSON export to {output_path}")
    
    try:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
        # Prepare export content
        export_content = {
            "data": data,
            "metadata": metadata or {}
        }
    
        # Write JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_content, f, indent=2, default=str)
    
        # Validate file size
        file_size = output_path.stat().st_size
        if file_size > MAX_EXPORT_FILE_SIZE:
            error_msg = f"Export file size ({file_size} bytes) exceeds limit ({MAX_EXPORT_FILE_SIZE} bytes)"
            logger.error(error_msg)
            # Remove the oversized file
            output_path.unlink()
            return ExportResult(
                success=False,
                file_path=str(output_path),
                file_size_bytes=file_size,
                message=error_msg,
                warnings=[]
            )
    
        logger.info(f"JSON export successful: {file_size} bytes")
        return ExportResult(
            success=True,
            file_path=str(output_path),
            file_size_bytes=file_size,
            message="JSON export completed successfully",
            warnings=[]
        )
    
    except Exception as e:
        logger.error(f"JSON export failed: {str(e)}")
        return ExportResult(
            success=False,
            file_path=str(output_path),
            file_size_bytes=0,
            message=f"JSON export failed: {str(e)}",
            warnings=[str(e)]
        )


def run_export_pipeline(
    analysis_results: Dict[str, Any],
    output_dir: str,
    metadata: Optional[Dict[str, Any]] = None,
    logger: Optional[logging.Logger] = None
) -> Dict[str, ExportResult]:
    """
    Run the complete export pipeline for analysis results.
    
    Args:
        analysis_results: Dictionary containing analysis results
        output_dir: Directory where output files will be written
        metadata: Optional metadata to include in JSON export
        logger: Logger instance for operation logging
    
    Returns:
        Dictionary mapping export types to ExportResult objects
    """
    if logger is None:
        logger = get_export_logger()
    
    logger.info("Starting export pipeline")
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = output_dir / "analysis_results.csv"
    json_path = output_dir / "analysis_results.json"
    
    csv_result = export_to_csv(analysis_results, str(csv_path), logger)
    json_result = export_to_json(analysis_results, str(json_path), metadata, logger)
    
    logger.info(f"Export pipeline completed: CSV={csv_result.success}, JSON={json_result.success}")
    
    return {
        "csv": csv_result,
        "json": json_result
    }


def main():
    """Main function for testing the export module."""
    # Setup logging
    logger = get_export_logger()
    
    # Sample data for testing
    sample_data = {
        "anova_results": {
            "f_statistic": 12.5,
            "p_value": 0.001,
            "degrees_of_freedom": [2, 150]
        },
        "effect_sizes": {
            "cohens_d": 0.8,
            "confidence_interval": [0.5, 1.1]
        },
        "metadata": {
            "analysis_date": "2024-01-15",
            "sample_size": 153
        }
    }
    
    output_dir = "data/output/test_exports"
    
    # Run export pipeline
    results = run_export_pipeline(
        analysis_results=sample_data,
        output_dir=output_dir,
        metadata={"test_run": True},
        logger=logger
    )
    
    # Print results
    for export_type, result in results.items():
        logger.info(f"{export_type.upper()} Export: {result.message}")
        if result.file_size_bytes > 0:
            logger.info(f"  File size: {result.file_size_bytes} bytes")
    
    return results

if __name__ == "__main__":
    main()