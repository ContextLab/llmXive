"""
Output serialization module for analysis results.

Provides functions to save and load AnalysisResult objects to/from JSON and Parquet formats.
Ensures all metadata, statistical estimates, and sensitivity data are preserved.
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


def _ensure_directory(filepath: Union[str, Path]) -> None:
    """Ensure the directory for the given filepath exists."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)


def _serialize_analysis_result(result: AnalysisResult) -> Dict[str, Any]:
    """
    Convert an AnalysisResult object to a serializable dictionary.
    
    Handles nested objects like sensitivity data and converts types 
    that JSON/Parquet don't natively support (e.g., numpy types, sets).
    """
    data = result.model_dump()
    
    # Ensure datetime is ISO string
    if isinstance(data.get('timestamp'), datetime):
        data['timestamp'] = data['timestamp'].isoformat()
    
    # Convert any nested numpy types in sensitivity data
    if 'sensitivity_data' in data and data['sensitivity_data']:
        serialized_sensitivity = []
        for item in data['sensitivity_data']:
            serializable_item = {}
            for k, v in item.items():
                if hasattr(v, 'item'):  # numpy scalar
                    serializable_item[k] = v.item()
                elif isinstance(v, (set, frozenset)):
                    serializable_item[k] = list(v)
                else:
                    serializable_item[k] = v
            serialized_sensitivity.append(serializable_item)
        data['sensitivity_data'] = serialized_sensitivity

    return data


def save_analysis_result(
    result: AnalysisResult,
    filepath: Union[str, Path],
    format: str = "json"
) -> Path:
    """
    Save an AnalysisResult to disk in JSON or Parquet format.
    
    Args:
        result: The AnalysisResult object to save.
        filepath: Path to the output file.
        format: Output format ('json' or 'parquet').
    
    Returns:
        The absolute path to the saved file.
    
    Raises:
        ValueError: If format is not 'json' or 'parquet'.
        FileNotFoundError: If the parent directory does not exist and cannot be created.
        TypeError: If the result contains non-serializable objects.
    """
    path = Path(filepath)
    _ensure_directory(path)
    
    data = _serialize_analysis_result(result)
    
    if format.lower() == "json":
        logger.info(f"Saving analysis result to JSON: {path}")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
    elif format.lower() == "parquet":
        logger.info(f"Saving analysis result to Parquet: {path}")
        # Flatten for Parquet: put scalar fields in one row, sensitivity in a nested structure or separate table
        # For simplicity and compatibility, we store the main result as a single-row DataFrame
        # and sensitivity data as a JSON string column or a separate file if needed.
        # Here we choose to store sensitivity data as a JSON string in the Parquet table.
        row_data = {}
        for k, v in data.items():
            if k == 'sensitivity_data' and isinstance(v, list):
                row_data[k] = json.dumps(v)
            else:
                row_data[k] = v
        
        df = pd.DataFrame([row_data])
        table = pa.Table.from_pandas(df)
        pq.write_table(table, path)
    else:
        raise ValueError(f"Unsupported format: {format}. Use 'json' or 'parquet'.")
    
    logger.info(f"Successfully saved analysis result to {path}")
    return path.resolve()


def load_analysis_result(
    filepath: Union[str, Path],
    format: Optional[str] = None
) -> AnalysisResult:
    """
    Load an AnalysisResult from disk (JSON or Parquet).
    
    Args:
        filepath: Path to the input file.
        format: Format of the file. If None, inferred from extension.
    
    Returns:
        The deserialized AnalysisResult object.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the format is unsupported or cannot be inferred.
        pydantic.ValidationError: If the loaded data does not match the AnalysisResult schema.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    if format is None:
        suffix = path.suffix.lower()
        if suffix == '.json':
            format = 'json'
        elif suffix in ['.parquet', '.pq']:
            format = 'parquet'
        else:
            raise ValueError(f"Cannot infer format from extension '{suffix}'. Specify 'json' or 'parquet'.")
    
    logger.info(f"Loading analysis result from {path} (format: {format})")
    
    if format.lower() == "json":
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    elif format.lower() == "parquet":
        table = pq.read_table(path)
        df = table.to_pandas()
        # Convert sensitivity JSON string back to list if present
        if 'sensitivity_data' in df.columns and df['sensitivity_data'].dtype == object:
            # Assume first row (single row table)
            raw_sens = df.iloc[0]['sensitivity_data']
            if isinstance(raw_sens, str):
                df.at[0, 'sensitivity_data'] = json.loads(raw_sens)
        data = df.iloc[0].to_dict()
    else:
        raise ValueError(f"Unsupported format: {format}. Use 'json' or 'parquet'.")
    
    # Reconstruct AnalysisResult
    # Handle timestamp string back to datetime if needed by model
    if 'timestamp' in data and isinstance(data['timestamp'], str):
        try:
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        except ValueError:
            pass # Let pydantic handle validation error if format is wrong
    
    return AnalysisResult(**data)
