"""
Translation module for converting heterogeneous modalities to text representations.
Implements the Unified Translator pattern for the Heterogeneous Scientific Foundation Model Collaboration Benchmark.
"""

import logging
import numpy as np
from typing import Dict, Any, List, Union, Optional, Tuple
from pathlib import Path
import pandas as pd
from src.utils.logging import get_logger

logger = get_logger(__name__)


def timeseries_to_text(data: Union[np.ndarray, List[List[float]], pd.DataFrame], label_name: str) -> str:
    """
    Convert time-series data to a deterministic text representation.
    
    This function implements the US-3 Scenario 1 schema:
    "Mean {label} = X {unit}, max = Y {unit}, min = Z {unit}, std = W {unit} "
    
    All quantitative information (mean, max, min, std) is retained in the text representation.
    The format is deterministic and suitable for LLM input.
    
    Args:
        data: Time-series data. Can be:
            - 1D numpy array or list of floats (single channel)
            - 2D numpy array or list of lists (multi-channel, each row is a channel)
            - pandas DataFrame (each column is a channel)
        label_name: Name of the variable being measured (e.g., "heart rate").
                    Used to format the output text.
                    
    Returns:
        A string representation of the time-series statistics.
        
    Example:
        >>> data = [1.0, 2.0, 3.0, 4.0, 5.0]
        >>> timeseries_to_text(data, "heart rate")
        'Mean heart rate = 3.0 bpm, max = 5.0 bpm, min = 1.0 bpm, std = 1.58 bpm '
    """
    # Convert input to numpy array for consistent processing
    if isinstance(data, pd.DataFrame):
        # If DataFrame, process each column separately or aggregate if single column
        if len(data.columns) == 1:
            series = data.iloc[:, 0].values
        else:
            # For multi-column, we aggregate across all values or process per column
            # For simplicity in unified mode, we aggregate all values into one summary
            series = data.values.flatten()
    elif isinstance(data, list):
        series = np.array(data, dtype=float).flatten()
    elif isinstance(data, np.ndarray):
        series = data.flatten()
    else:
        raise TypeError(f"Unsupported data type: {type(data)}. Expected array-like or DataFrame.")
    
    # Remove NaN values for calculation
    valid_series = series[~np.isnan(series)]
    
    if len(valid_series) == 0:
        logger.warning("Time-series data contains only NaN values. Returning empty statistics.")
        return f"Mean {label_name} = N/A, max = N/A, min = N/A, std = N/A "
    
    # Calculate statistics
    mean_val = np.mean(valid_series)
    max_val = np.max(valid_series)
    min_val = np.min(valid_series)
    std_val = np.std(valid_series)
    
    # Determine appropriate unit suffix based on label_name
    # This is a simple heuristic; in a real system, units would be metadata
    unit = "bpm" if "heart" in label_name.lower() or "rate" in label_name.lower() else "units"
    
    # Format the text representation
    # Using 2 decimal places for consistency
    text = (
        f"Mean {label_name} = {mean_val:.2f} {unit}, "
        f"max = {max_val:.2f} {unit}, "
        f"min = {min_val:.2f} {unit}, "
        f"std = {std_val:.2f} {unit} "
    )
    
    logger.debug(f"Converted time-series to text: {text}")
    return text


def tabular_to_text(df: Union[pd.DataFrame, List[Dict]], label_column: Optional[str] = None) -> str:
    """
    Convert tabular data to a deterministic text representation.
    
    Creates a CSV-style text representation with column names and values.
    
    Args:
        df: Tabular data as pandas DataFrame or list of dictionaries.
        label_column: Optional name of the label/target column.
                    
    Returns:
        A string representation of the tabular data.
    """
    if isinstance(df, list):
        df = pd.DataFrame(df)
    
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Unsupported data type: {type(df)}. Expected DataFrame or list of dicts.")
    
    # Handle empty dataframe
    if df.empty:
        return "Empty table"
    
    # Convert all values to string for consistent text representation
    # Replace NaN with 'null' for text representation
    df_text = df.fillna('null')
    
    # Build text representation
    lines = []
    columns = df_text.columns.tolist()
    
    # Header
    lines.append(" | ".join(columns))
    lines.append("-" * (len(" | ".join(columns))))
    
    # Rows
    for _, row in df_text.iterrows():
        row_str = " | ".join(str(v) for v in row.values)
        lines.append(row_str)
    
    text = "\n".join(lines)
    
    if label_column:
        text += f"\nLabel column: {label_column}"
    
    logger.debug(f"Converted tabular data to text (length: {len(text)} chars)")
    return text


def validate_translation(original_data: Any, translated_text: str, threshold: float = 0.8) -> float:
    """
    Validate the fidelity of a translation from structured data to text.
    
    Measures information loss by checking if key statistical properties
    can be recovered from the text representation.
    
    Args:
        original_data: The original structured data (array, DataFrame, etc.)
        translated_text: The text representation generated by timeseries_to_text or tabular_to_text
        threshold: Minimum fidelity score to consider the translation valid
                    
    Returns:
        Fidelity score between 0.0 and 1.0
    """
    # For time-series data, we check if the text contains the expected statistical markers
    if isinstance(original_data, (np.ndarray, list)):
        # Convert to array for stats
        if isinstance(original_data, list):
            arr = np.array(original_data).flatten()
        else:
            arr = original_data.flatten()
        
        valid_arr = arr[~np.isnan(arr)]
        if len(valid_arr) == 0:
            return 0.0
        
        # Calculate original stats
        orig_mean = np.mean(valid_arr)
        orig_max = np.max(valid_arr)
        orig_min = np.min(valid_arr)
        orig_std = np.std(valid_arr)
        
        # Extract stats from text (simple regex-like parsing)
        # This is a heuristic check - in production, use proper parsing
        import re
        numbers = re.findall(r'[-+]?\d*\.\d+|\d+', translated_text)
        if len(numbers) < 4:
            logger.warning("Could not extract sufficient statistics from translated text")
            return 0.5
        
        # Compare extracted vs original (normalized difference)
        # This is a simplified fidelity check
        try:
            extracted = [float(n) for n in numbers]
            # Check if the range of extracted numbers covers the original stats
            # This is a rough approximation
            fidelity = 1.0
            for i, orig_stat in enumerate([orig_mean, orig_max, orig_min, orig_std]):
                if i < len(extracted):
                    # Calculate relative error
                    if orig_stat != 0:
                        rel_error = abs(extracted[i] - orig_stat) / abs(orig_stat)
                    else:
                        rel_error = abs(extracted[i])
                    fidelity *= max(0, 1 - rel_error)
            
            fidelity = fidelity ** (1/4)  # Geometric mean
            
        except (ValueError, IndexError):
            fidelity = 0.0
            
    elif isinstance(original_data, pd.DataFrame):
        # For tabular data, check if column names and row count are preserved
        if " | " in translated_text:
            # Basic check: text contains column separators
            fidelity = 0.9
            if len(original_data) > 0:
                # Check if row count is mentioned or implied
                rows_in_text = translated_text.count("\n") - 1
                if rows_in_text >= len(original_data):
                    fidelity = 1.0
        else:
            fidelity = 0.0
    else:
        logger.warning("Cannot validate translation for unknown data type")
        fidelity = 0.0
    
    if fidelity < threshold:
        logger.warning(f"Translation fidelity {fidelity:.2f} below threshold {threshold}")
    
    return fidelity


class UnifiedTranslator:
    """
    Unified Translator class for converting all modalities to text.
    
    This class provides a consistent interface for translating heterogeneous
    data modalities (time-series, tabular, text) into a unified text representation
    suitable for feeding into a single LLM.
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.translation_log = []
    
    def translate_timeseries(self, data: Union[np.ndarray, List, pd.DataFrame], label_name: str = "value") -> str:
        """
        Translate time-series data to text.
        
        Args:
            data: Time-series data
            label_name: Name of the measured variable
                    
        Returns:
            Text representation of the time-series
        """
        result = timeseries_to_text(data, label_name)
        self.translation_log.append({
            "type": "timeseries",
            "label": label_name,
            "output_length": len(result)
        })
        return result
    
    def translate_tabular(self, df: Union[pd.DataFrame, List[Dict]], label_column: Optional[str] = None) -> str:
        """
        Translate tabular data to text.
        
        Args:
            df: Tabular data
            label_column: Name of the target column
                    
        Returns:
            Text representation of the tabular data
        """
        result = tabular_to_text(df, label_column)
        self.translation_log.append({
            "type": "tabular",
            "columns": list(df.columns) if isinstance(df, pd.DataFrame) else [],
            "output_length": len(result)
        })
        return result
    
    def translate_all(self, modalities_dict: Dict[str, Any]) -> str:
        """
        Translate all modalities in a dictionary to a combined text representation.
        
        Args:
            modalities_dict: Dictionary with keys as modality names and values as data
                    
        Returns:
            Combined text representation of all modalities
        """
        parts = []
        for modality, data in modalities_dict.items():
            if modality == "timeseries":
                label = modalities_dict.get("timeseries_label", "value")
                text = self.translate_timeseries(data, label)
            elif modality == "tabular":
                label = modalities_dict.get("tabular_label", None)
                text = self.translate_tabular(data, label)
            elif modality == "text":
                # Text modality is already text, just pass through
                text = str(data)
            else:
                self.logger.warning(f"Unknown modality type: {modality}, skipping")
                continue
            
            parts.append(f"[{modality.upper()}]: {text}")
        
        combined = "\n".join(parts)
        self.translation_log.append({
            "type": "combined",
            "modalities": list(modalities_dict.keys()),
            "output_length": len(combined)
        })
        
        return combined
    
    def get_translation_log(self) -> List[Dict]:
        """Return the log of all translations performed."""
        return self.translation_log
    
    def clear_log(self):
        """Clear the translation log."""
        self.translation_log = []


def main():
    """
    Main function for testing the translation module.
    This function demonstrates the usage of timeseries_to_text and tabular_to_text.
    """
    print("Testing timeseries_to_text...")
    
    # Test with 1D array
    ts_data = np.array([72.5, 73.0, 74.2, 71.8, 73.5, 74.0, 72.9])
    ts_text = timeseries_to_text(ts_data, "heart rate")
    print(f"Time-series text: {ts_text}")
    
    # Validate translation
    fidelity = validate_translation(ts_data, ts_text)
    print(f"Fidelity score: {fidelity:.2f}")
    
    # Test with DataFrame
    df_data = pd.DataFrame({
        'age': [25, 30, 35],
        'blood_pressure': [120, 130, 125],
        'cholesterol': [200, 220, 210]
    })
    tab_text = tabular_to_text(df_data, 'blood_pressure')
    print(f"Tabular text:\n{tab_text}")
    
    # Test UnifiedTranslator
    translator = UnifiedTranslator()
    combined = translator.translate_all({
        "timeseries": ts_data,
        "timeseries_label": "heart rate",
        "tabular": df_data,
        "tabular_label": "blood_pressure"
    })
    print(f"\nCombined translation:\n{combined}")
    
    print("\nTranslation module tests completed.")


if __name__ == "__main__":
    main()