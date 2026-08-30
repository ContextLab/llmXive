"""
Serialization module for AnalysisResult objects.

Provides functionality to save causal analysis results (ATT, p-values, confidence
intervals, methodology details, and sensitivity data) to JSON and Parquet formats.

This module consumes the AnalysisResult Pydantic model defined in schemas.py
and ensures type-safe, validated serialization.
"""
import json
import pandas as pd
from pathlib import Path
from typing import Optional, Union, Dict, Any, List
from datetime import datetime
import pyarrow as pa
import pyarrow.parquet as pq
from src.models.schemas import AnalysisResult
from src.utils.logging import get_logger

logger = get_logger(__name__)


def save_analysis_result(
    result: AnalysisResult,
    output_path: str,
    format: str = "json"
) -> Path:
    """
    Save an AnalysisResult object to disk in the specified format.
    
    Args:
        result: The validated AnalysisResult object containing ATT, p-value,
                confidence intervals, methodology, and sensitivity data.
        output_path: Path where the output file will be written.
        format: Output format, either "json" or "parquet".
    
    Returns:
        Path object pointing to the created file.
    
    Raises:
        ValueError: If format is not "json" or "parquet".
        FileNotFoundError: If the directory for output_path does not exist.
    """
    output_path_obj = Path(output_path)
    
    # Ensure output directory exists
    if not output_path_obj.parent.exists():
        raise FileNotFoundError(
            f"Output directory does not exist: {output_path_obj.parent}"
        )
    
    if format.lower() == "json":
        return _save_to_json(result, output_path_obj)
    elif format.lower() == "parquet":
        return _save_to_parquet(result, output_path_obj)
    else:
        raise ValueError(
            f"Unsupported format: {format}. Must be 'json' or 'parquet'."
        )


def _save_to_json(result: AnalysisResult, output_path: Path) -> Path:
    """
    Serialize AnalysisResult to JSON.
    
    Pydantic models have a built-in .model_dump() method that handles
    nested structures and type serialization.
    """
    logger.info(f"Saving analysis result to JSON: {output_path}")
    
    # Convert to dictionary, handling datetime and nested structures
    data = result.model_dump(mode="json")
    
    # Add metadata about the export
    data["_exported_at"] = datetime.utcnow().isoformat()
    data["_export_version"] = "1.0"
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    
    logger.info(f"Successfully saved analysis result to {output_path}")
    return output_path


def _save_to_parquet(result: AnalysisResult, output_path: Path) -> Path:
    """
    Serialize AnalysisResult to Parquet.
    
    Parquet is better for large datasets and columnar analysis.
    We flatten the nested structure into a single-row DataFrame.
    """
    logger.info(f"Saving analysis result to Parquet: {output_path}")
    
    # Flatten the result into a dictionary suitable for a single-row DataFrame
    data = {
        "att_estimate": [result.att_estimate],
        "att_std_error": [result.att_std_error],
        "p_value": [result.p_value],
        "ci_lower": [result.confidence_interval[0]],
        "ci_upper": [result.confidence_interval[1]],
        "methodology": [result.methodology],
        "balance_status": [result.balance_status],
        "placebo_passed": [result.placebo_passed],
        "n_treatment": [result.n_treatment],
        "n_control": [result.n_control],
        "caliper_used": [result.caliper_used],
        "exported_at": [datetime.utcnow().isoformat()],
        "export_version": ["1.0"]
    }
    
    # Include sensitivity analysis as a JSON string in a single cell
    if result.sensitivity_analysis:
        data["sensitivity_analysis"] = [json.dumps(result.sensitivity_analysis)]
    else:
        data["sensitivity_analysis"] = [None]
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to Parquet
    df.to_parquet(output_path, index=False, engine="pyarrow")
    
    logger.info(f"Successfully saved analysis result to {output_path}")
    return output_path


def load_analysis_result(input_path: str, format: str = "json") -> AnalysisResult:
    """
    Load an AnalysisResult object from disk.
    
    Args:
        input_path: Path to the input file.
        format: Input format, either "json" or "parquet".
    
    Returns:
        Validated AnalysisResult object.
    
    Raises:
        ValueError: If format is not supported or file is malformed.
        FileNotFoundError: If the input file does not exist.
    """
    input_path_obj = Path(input_path)
    
    if not input_path_obj.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    if format.lower() == "json":
        return _load_from_json(input_path_obj)
    elif format.lower() == "parquet":
        return _load_from_parquet(input_path_obj)
    else:
        raise ValueError(
            f"Unsupported format: {format}. Must be 'json' or 'parquet'."
        )


def _load_from_json(input_path: Path) -> AnalysisResult:
    """Load and validate from JSON."""
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Remove metadata fields added during export
    data.pop("_exported_at", None)
    data.pop("_export_version", None)
    
    return AnalysisResult(**data)


def _load_from_parquet(input_path: Path) -> AnalysisResult:
    """Load and validate from Parquet."""
    df = pd.read_parquet(input_path, engine="pyarrow")
    
    if df.empty:
        raise ValueError(f"Parquet file is empty: {input_path}")
    
    # Extract first row
    row = df.iloc[0]
    
    # Parse sensitivity analysis if present
    sensitivity = None
    if pd.notna(row.get("sensitivity_analysis")):
        sensitivity = json.loads(row["sensitivity_analysis"])
    
    # Construct AnalysisResult
    return AnalysisResult(
        att_estimate=row["att_estimate"],
        att_std_error=row["att_std_error"],
        p_value=row["p_value"],
        confidence_interval=(row["ci_lower"], row["ci_upper"]),
        methodology=row["methodology"],
        balance_status=row["balance_status"],
        placebo_passed=row["placebo_passed"],
        n_treatment=int(row["n_treatment"]),
        n_control=int(row["n_control"]),
        caliper_used=row["caliper_used"],
        sensitivity_analysis=sensitivity
    )
