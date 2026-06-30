"""
Unified translation layer for converting heterogeneous data modalities to text.
Implements FR-003: Unified Text-Only Translation.
"""
import logging
import numpy as np
from typing import Dict, Any, List, Union, Optional, Tuple
from pathlib import Path

from src.utils.logging import get_logger

logger = get_logger(__name__)


class UnifiedTranslator:
    """
    Translates time-series, tabular, and other modalities into deterministic text
    representations suitable for feeding into a single LLM.
    """

    def __init__(self, fidelity_threshold: float = 0.85):
        """
        Initialize the translator.

        Args:
            fidelity_threshold: Minimum acceptable fidelity score (0.0 to 1.0)
        """
        self.fidelity_threshold = fidelity_threshold
        logger.info(f"UnifiedTranslator initialized with fidelity threshold: {fidelity_threshold}")

    def translate_timeseries(self, input_data: Union[np.ndarray, List[List[float]], Dict[str, Any]], label_name: Optional[str] = None) -> str:
        """
        Convert time-series data to a deterministic text description.

        Schema:
            "Mean {label} = {mean} {unit}, max = {max}, min = {min}, std = {std}, trend = {trend}"

        Args:
            input_data: Time-series data. Can be:
                - 1D numpy array or list of floats (single variable)
                - 2D numpy array or list of lists (multiple variables, columns)
                - Dict with 'values' (array) and 'label' (string)
            label_name: Optional label for the variable (e.g., "heart rate")

        Returns:
            Deterministic text string representation
        """
        try:
            # Normalize input to numpy array
            if isinstance(input_data, dict):
                values = np.array(input_data.get('values', []))
                label_name = input_data.get('label', label_name)
            elif isinstance(input_data, (list, np.ndarray)):
                values = np.array(input_data)
            else:
                raise ValueError(f"Unsupported input type for timeseries: {type(input_data)}")

            if values.ndim == 0:
                values = np.array([values])

            if values.ndim > 1:
                # If 2D, assume multiple variables; flatten or process column-wise
                # For simplicity, we process each column and concatenate
                if values.shape[1] == 1:
                    values = values.flatten()
                else:
                    # Multi-variate: describe each column
                    descriptions = []
                    for i in range(values.shape[1]):
                        col = values[:, i]
                        desc = self._describe_1d_timeseries(col, f"Variable {i+1}")
                        descriptions.append(desc)
                    return " | ".join(descriptions)

            # Single variable case
            desc = self._describe_1d_timeseries(values, label_name)
            return desc

        except Exception as e:
            logger.error(f"Error translating time-series: {e}")
            raise

    def _describe_1d_timeseries(self, values: np.ndarray, label_name: str) -> str:
        """Generate description for 1D time-series."""
        if len(values) == 0:
            return f"{label_name}: No data"

        mean_val = np.mean(values)
        max_val = np.max(values)
        min_val = np.min(values)
        std_val = np.std(values)

        # Simple trend detection: compare first half mean vs second half mean
        mid = len(values) // 2
        if mid > 0:
            first_half_mean = np.mean(values[:mid])
            second_half_mean = np.mean(values[mid:])
            if second_half_mean > first_half_mean * 1.05:
                trend = "increasing"
            elif second_half_mean < first_half_mean * 0.95:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "insufficient data"

        # Format numbers consistently
        desc = (
            f"Mean {label_name} = {mean_val:.4f}, "
            f"max = {max_val:.4f}, "
            f"min = {min_val:.4f}, "
            f"std = {std_val:.4f}, "
            f"trend = {trend}"
        )
        return desc

    def translate_tabular(self, df: Any, label_column: Optional[str] = None) -> str:
        """
        Convert tabular data to a deterministic text representation.

        Schema:
            "Row 1: col1=val1, col2=val2, ... | Row 2: ..."
            If label_column is provided, it is highlighted.

        Args:
            df: Pandas DataFrame or similar (must support .columns and .iloc)
            label_column: Name of the target label column

        Returns:
            Deterministic text string representation
        """
        try:
            # Handle list of dicts or dict of lists if not DataFrame
            if isinstance(df, dict):
                # Assume dict of lists, convert to simple row iteration
                keys = list(df.keys())
                rows = []
                for i in range(len(df[keys[0]])):
                    row_desc = ", ".join(f"{k}={df[k][i]}" for k in keys)
                    rows.append(f"Row {i+1}: {row_desc}")
                return " | ".join(rows)

            if isinstance(df, list):
                # List of dicts
                if not df:
                    return "No data"
                keys = list(df[0].keys())
                rows = []
                for i, row in enumerate(df):
                    row_desc = ", ".join(f"{k}={row[k]}" for k in keys)
                    rows.append(f"Row {i+1}: {row_desc}")
                return " | ".join(rows)

            # Pandas-like
            if label_column and label_column in df.columns:
                # Highlight label column in description
                cols = list(df.columns)
                label_idx = cols.index(label_column)
                cols_reordered = [label_column] + [c for c in cols if c != label_column]
            else:
                cols_reordered = list(df.columns)

            rows = []
            for i in range(len(df)):
                row_vals = []
                for col in cols_reordered:
                  val = df.iloc[i][col]
                  if isinstance(val, float):
                      val_str = f"{val:.4f}"
                  else:
                      val_str = str(val)
                  row_vals.append(f"{col}={val_str}")
                row_desc = ", ".join(row_vals)
                rows.append(f"Row {i+1}: {row_desc}")

            return " | ".join(rows)

        except Exception as e:
            logger.error(f"Error translating tabular data: {e}")
            raise

    def translate_all(self, modalities_dict: Dict[str, Any], label_column: Optional[str] = None) -> str:
        """
        Translate all modalities in a dictionary and combine into a single text.

        Args:
            modalities_dict: Dictionary with keys as modality names (e.g., 'timeseries', 'tabular')
                             and values as the data.
            label_column: Optional label column name for tabular data

        Returns:
            Combined text representation
        """
        parts = []
        for modality, data in modalities_dict.items():
            if data is None:
                continue
            if modality == "timeseries":
                text = self.translate_timeseries(data, label_name="timeseries_value")
            elif modality == "tabular":
                text = self.translate_tabular(data, label_column=label_column)
            elif modality == "text":
                # Already text, just pass through
                text = str(data)
            else:
                logger.warning(f"Unknown modality type: {modality}, skipping")
                continue
            parts.append(f"[{modality.upper()}]: {text}")

        return " | ".join(parts)

    def validate_translation(self, original_data: Any, translated_text: str) -> float:
        """
        Validate the quality of translation by measuring information retention.

        This is a heuristic validation. For time-series, it checks if key statistics
        mentioned in the text can be roughly reconstructed. For tabular, it checks
        if row count and column names are preserved.

        Args:
            original_data: Original data (array, DataFrame, etc.)
            translated_text: The generated text

        Returns:
            Fidelity score between 0.0 and 1.0
        """
        score = 0.0
        total_checks = 0

        try:
            # Check 1: Text length (basic sanity)
            total_checks += 1
            if len(translated_text) > 20:
                score += 0.2
            else:
                logger.warning("Translation text too short, possible data loss")

            # Check 2: Presence of key keywords based on data type
            total_checks += 1
            keywords = []
            if isinstance(original_data, (np.ndarray, list)):
                keywords = ["mean", "max", "min", "std"]
            elif hasattr(original_data, 'columns'):  # DataFrame-like
                keywords = [str(col) for col in original_data.columns] + ["Row"]
            elif isinstance(original_data, dict):
                keywords = list(original_data.keys())

            for kw in keywords:
                if kw.lower() in translated_text.lower():
                    score += 0.1
                    break  # One point per type, not per keyword

            # Check 3: Numeric presence for time-series
            if isinstance(original_data, (np.ndarray, list)):
                total_checks += 1
                if any(c.isdigit() for c in translated_text):
                    score += 0.3
                else:
                    logger.warning("No numbers found in translation for numeric data")

            # Check 4: Row count approximation for tabular
            if hasattr(original_data, 'shape'):
                total_checks += 1
                if "Row" in translated_text:
                    # Count "Row" occurrences as proxy for row count
                    row_count_text = translated_text.count("Row")
                    actual_row_count = original_data.shape[0]
                    if row_count_text == actual_row_count:
                        score += 0.3
                    elif row_count_text > 0 and actual_row_count > 0:
                        score += 0.15
                else:
                    logger.warning("No row indicators found for tabular data")

        except Exception as e:
            logger.error(f"Error during fidelity validation: {e}")
            return 0.0

        final_score = min(score / (total_checks or 1), 1.0)

        if final_score < self.fidelity_threshold:
            logger.warning(
                f"Translation fidelity {final_score:.2f} below threshold {self.fidelity_threshold}. "
                f"Original type: {type(original_data)}, Text length: {len(translated_text)}"
            )

        return final_score


def main():
    """
    CLI entry point for testing translation functionality.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Unified Translator CLI")
    parser.add_argument("--mode", type=str, choices=["timeseries", "tabular", "all"], default="timeseries")
    parser.add_argument("--fidelity-threshold", type=float, default=0.85)
    args = parser.parse_args()

    translator = UnifiedTranslator(fidelity_threshold=args.fidelity_threshold)

    if args.mode == "timeseries":
        # Sample time-series data
        data = np.random.randn(100).cumsum() + 50
        text = translator.translate_timeseries(data, label_name="sensor_reading")
        print(f"Translated Time-Series:\n{text}")
        fidelity = translator.validate_translation(data, text)
        print(f"Fidelity Score: {fidelity:.4f}")

    elif args.mode == "tabular":
        try:
            import pandas as pd
            df = pd.DataFrame({
                "feature_a": np.random.randn(5),
                "feature_b": np.random.randn(5),
                "label": np.random.choice([0, 1], 5)
            })
            text = translator.translate_tabular(df, label_column="label")
            print(f"Translated Tabular:\n{text}")
            fidelity = translator.validate_translation(df, text)
            print(f"Fidelity Score: {fidelity:.4f}")
        except ImportError:
            print("Pandas not installed, skipping tabular test.")

    elif args.mode == "all":
        # Mock data for all modalities
        ts_data = np.random.randn(50)
        tab_data = {"col1": [1, 2], "col2": [3.5, 4.1], "target": [0, 1]}
        modalities = {"timeseries": ts_data, "tabular": tab_data}
        text = translator.translate_all(modalities, label_column="target")
        print(f"Translated All:\n{text}")
        fidelity = translator.validate_translation(modalities, text)
        print(f"Fidelity Score: {fidelity:.4f}")


if __name__ == "__main__":
    main()
