import logging
import numpy as np
from typing import Dict, Any, List, Union, Optional, Tuple
from pathlib import Path
import pandas as pd
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Default fidelity threshold (configurable via environment or argument)
DEFAULT_FIDELITY_THRESHOLD = 0.85

def timeseries_to_text(data: Union[np.ndarray, List[float], pd.Series], label_name: Optional[str] = None) -> str:
    """
    Convert time-series data to a deterministic text representation.
    
    Args:
        data: 1D array-like time-series data
        label_name: Optional label for the series (e.g., "heart_rate")
    
    Returns:
        String representation with statistical summary
    """
    if isinstance(data, list):
        data = np.array(data)
    elif isinstance(data, pd.Series):
        data = data.values
    
    # Ensure 1D
    if data.ndim != 1:
        raise ValueError(f"Expected 1D time-series, got shape {data.shape}")
    
    if len(data) == 0:
        return "Time-series is empty."
    
    mean_val = np.mean(data)
    max_val = np.max(data)
    min_val = np.min(data)
    std_val = np.std(data)
    median_val = np.median(data)
    
    # Format with consistent precision
    text = f"Time-series stats: mean={mean_val:.4f}, std={std_val:.4f}, "
    text += f"min={min_val:.4f}, max={max_val:.4f}, median={median_val:.4f}"
    
    if label_name:
        text = f"{label_name.capitalize()}: {text}"
    
    return text

def tabular_to_text(df: pd.DataFrame, label_column: Optional[str] = None) -> str:
    """
    Convert tabular data (DataFrame) to a deterministic text representation.
    
    Args:
        df: Pandas DataFrame
        label_column: Optional name of the label/target column
    
    Returns:
        String representation with column values
    """
    if df.empty:
        return "Table is empty."
    
    rows = []
    for idx, row in df.iterrows():
        row_parts = []
        for col in df.columns:
            val = row[col]
            # Format numeric values consistently
            if isinstance(val, (int, float, np.number)):
                if np.isnan(val):
                    val_str = "NaN"
                elif isinstance(val, float):
                    val_str = f"{val:.6f}"
                else:
                    val_str = str(val)
            else:
                val_str = str(val)
            row_parts.append(f"{col}={val_str}")
        
        row_text = ", ".join(row_parts)
        if label_column and label_column in df.columns:
            # Highlight label if present
            label_val = row[label_column]
            row_text += f" [LABEL={label_val}]"
        
        rows.append(f"Row {idx}: {row_text}")
    
    return "; ".join(rows)

def validate_translation(original_data: Union[np.ndarray, List, pd.DataFrame, Dict], 
                         translated_text: str, 
                         threshold: float = DEFAULT_FIDELITY_THRESHOLD) -> float:
    """
    Validate the quality of a translation by measuring information loss.
    
    This function compares the statistical properties of the original data
    against the information preserved in the translated text.
    
    Args:
        original_data: The original numerical data (array, list, or DataFrame)
        translated_text: The generated text representation
        threshold: Minimum acceptable fidelity score (default 0.85)
    
    Returns:
        Fidelity score between 0.0 and 1.0, where 1.0 is perfect preservation.
    
    Note:
        - For time-series: Checks if mean, std, min, max, median are present in text.
        - For tabular: Checks if column names and numeric values are present.
        - Returns 0.0 if translation text is empty or malformed.
    """
    if not translated_text or not isinstance(translated_text, str):
        logger.warning("Translation text is empty or invalid.")
        return 0.0
    
    text_lower = translated_text.lower()
    
    if isinstance(original_data, pd.DataFrame):
        # Tabular validation
        if original_data.empty:
            return 1.0 if "empty" in text_lower else 0.0
        
        # Check for presence of column names
        columns_present = 0
        total_columns = len(original_data.columns)
        
        for col in original_data.columns:
            if str(col).lower() in text_lower:
                columns_present += 1
        
        column_score = columns_present / total_columns if total_columns > 0 else 0.0
        
        # Check for numeric patterns (simple heuristic)
        # Count digits in text vs expected from data
        text_digits = sum(c.isdigit() for c in translated_text)
        # Estimate expected digits (very rough heuristic: 6 decimal places per value * num cells)
        expected_digits = len(original_data) * len(original_data.columns) * 6
        
        # Normalize digit count (cap at 1.0)
        digit_ratio = min(1.0, text_digits / max(1, expected_digits))
        
        # Combined score: weighted average
        fidelity = 0.6 * column_score + 0.4 * digit_ratio
        
    elif isinstance(original_data, (np.ndarray, list, pd.Series)):
        # Time-series validation
        if isinstance(original_data, list):
            original_data = np.array(original_data)
        elif isinstance(original_data, pd.Series):
            original_data = original_data.values
        
        if len(original_data) == 0:
            return 1.0 if "empty" in text_lower else 0.0
        
        # Calculate expected stats
        expected_stats = {
            'mean': np.mean(original_data),
            'std': np.std(original_data),
            'min': np.min(original_data),
            'max': np.max(original_data),
            'median': np.median(original_data)
        }
        
        # Check presence of each stat in text
        stats_found = 0
        total_stats = len(expected_stats)
        
        for name, value in expected_stats.items():
            # Convert value to string with similar precision as translator
            val_str = f"{value:.4f}"
            # Also check without leading zeros for robustness
            if val_str in translated_text or f"{value:.2f}" in translated_text:
                stats_found += 1
        
        fidelity = stats_found / total_stats if total_stats > 0 else 0.0
        
    else:
        logger.warning(f"Unsupported data type for fidelity validation: {type(original_data)}")
        return 0.0
    
    # Log warning if fidelity is below threshold
    if fidelity < threshold:
        logger.warning(f"Translation fidelity {fidelity:.4f} is below threshold {threshold}. "
                     "Significant information loss detected.")
    else:
        logger.debug(f"Translation fidelity {fidelity:.4f} meets threshold {threshold}.")
    
    return fidelity

class UnifiedTranslator:
    """
    Unified translator for heterogeneous data modalities to text.
    Supports time-series and tabular data translation with fidelity validation.
    """
    
    def __init__(self, fidelity_threshold: float = DEFAULT_FIDELITY_THRESHOLD):
        """
        Initialize the translator.
        
        Args:
            fidelity_threshold: Minimum acceptable fidelity score for translations.
        """
        self.fidelity_threshold = fidelity_threshold
        self.logger = get_logger(__name__)
    
    def translate_timeseries(self, input_data: Union[np.ndarray, List, pd.Series], 
                             label_name: Optional[str] = None) -> Tuple[str, float]:
        """
        Translate time-series data to text and validate fidelity.
        
        Args:
            input_data: 1D time-series data
            label_name: Optional label for the series
        
        Returns:
            Tuple of (translated_text, fidelity_score)
        """
        text = timeseries_to_text(input_data, label_name)
        fidelity = validate_translation(input_data, text, self.fidelity_threshold)
        return text, fidelity
    
    def translate_tabular(self, df: pd.DataFrame, label_column: Optional[str] = None) -> Tuple[str, float]:
        """
        Translate tabular data to text and validate fidelity.
        
        Args:
            df: Input DataFrame
            label_column: Optional label column name
        
        Returns:
            Tuple of (translated_text, fidelity_score)
        """
        text = tabular_to_text(df, label_column)
        fidelity = validate_translation(df, text, self.fidelity_threshold)
        return text, fidelity
    
    def translate_all(self, modalities_dict: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Translate all modalities in a dictionary.
        
        Args:
            modalities_dict: Dictionary mapping modality names to data
        
        Returns:
            Dictionary with translated text and fidelity scores for each modality
        """
        results = {}
        
        for modality, data in modalities_dict.items():
            if isinstance(data, pd.DataFrame):
                text, fidelity = self.translate_tabular(data)
            elif isinstance(data, (np.ndarray, list, pd.Series)):
                text, fidelity = self.translate_timeseries(data)
            else:
                self.logger.warning(f"Unsupported modality type for {modality}: {type(data)}")
                results[modality] = {
                    "text": "Unsupported data type",
                    "fidelity": 0.0,
                    "status": "error"
                }
                continue
            
            status = "ok" if fidelity >= self.fidelity_threshold else "warning"
            results[modality] = {
                "text": text,
                "fidelity": fidelity,
                "status": status
            }
        
        return results

def main():
    """
    Main entry point for testing the translation module.
    Demonstrates fidelity validation with sample data.
    """
    logger.info("Starting translation fidelity validation demo.")
    
    # Sample time-series data
    ts_data = np.random.randn(100) * 10 + 50
    ts_label = "heart_rate"
    
    # Sample tabular data
    df = pd.DataFrame({
        'age': [25, 30, 35],
        'income': [50000.50, 60000.75, 75000.25],
        'score': [0.85, 0.92, 0.78]
    })
    
    translator = UnifiedTranslator(fidelity_threshold=0.80)
    
    # Test time-series
    ts_text, ts_fidelity = translator.translate_timeseries(ts_data, ts_label)
    logger.info(f"Time-series translation: {ts_text}")
    logger.info(f"Time-series fidelity: {ts_fidelity:.4f}")
    
    # Test tabular
    tab_text, tab_fidelity = translator.translate_tabular(df, 'score')
    logger.info(f"Tabular translation: {tab_text}")
    logger.info(f"Tabular fidelity: {tab_fidelity:.4f}")
    
    # Test full dict
    multi_result = translator.translate_all({
        "ts": ts_data,
        "tab": df
    })
    
    for modality, result in multi_result.items():
        logger.info(f"Modality '{modality}' -> Fidelity: {result['fidelity']:.4f}, Status: {result['status']}")
    
    logger.info("Translation demo completed.")

if __name__ == "__main__":
    main()