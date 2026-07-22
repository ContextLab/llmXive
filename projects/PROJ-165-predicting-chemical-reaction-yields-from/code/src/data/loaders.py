"""
PyTorch Dataset classes for handling ReactionSample data.
Supports missing channels via masking and targets normalized DFT total molecular energy.
"""
import torch
from torch.utils.data import Dataset
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple, Optional, List, Any, Union
import logging

logger = logging.getLogger(__name__)


class ReactionSample(Dataset):
    """
    PyTorch Dataset for reaction samples containing spectral data, fingerprints,
    reaction conditions, and the target variable (normalized DFT total molecular energy).

    Handles missing channels (e.g., missing IR, Raman, or NMR spectra) via masking.
    """

    def __init__(
        self,
        data_path: Union[str, Path],
        target_column: str = "normalized_dft_energy",
        spectrum_columns: List[str] = None,
        fingerprint_column: str = "ecfp4_vector",
        condition_columns: List[str] = None,
        mask_missing: bool = True
    ):
        """
        Initialize the ReactionSample dataset.

        Args:
            data_path: Path to the CSV/Parquet file containing preprocessed data.
            target_column: Name of the column containing the target variable.
            spectrum_columns: List of column names containing spectral data.
            fingerprint_column: Name of the column containing the fingerprint vector.
            condition_columns: List of column names containing reaction condition features.
            mask_missing: If True, generate masks for missing spectrum data.
        """
        self.data_path = Path(data_path)
        self.target_column = target_column
        self.spectrum_columns = spectrum_columns or ["ir_spectrum", "raman_spectrum", "nmr_spectrum"]
        self.fingerprint_column = fingerprint_column
        self.condition_columns = condition_columns or []
        self.mask_missing = mask_missing

        # Load data
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_path}")

        logger.info(f"Loading dataset from {self.data_path}")
        if self.data_path.suffix == ".parquet":
            self.df = pd.read_parquet(self.data_path)
        else:
            self.df = pd.read_csv(self.data_path)

        logger.info(f"Loaded {len(self.df)} samples")

        # Validate required columns
        required_cols = [self.target_column, self.fingerprint_column] + self.spectrum_columns
        missing_cols = [col for col in required_cols if col not in self.df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in dataset: {missing_cols}")

        # Pre-convert string representations of arrays to numpy arrays if necessary
        self._preprocess_data()

        # Initialize masks if needed
        self.masks = self._generate_masks() if self.mask_missing else None

    def _preprocess_data(self):
        """Convert string representations of arrays to numpy arrays/tensors."""
        for col in self.spectrum_columns + [self.fingerprint_column] + self.condition_columns:
            if col in self.df.columns:
                # Check if column contains string representations of arrays
                if self.df[col].dtype == "object":
                    try:
                        self.df[col] = self.df[col].apply(lambda x: np.fromstring(x.strip("[]"), sep=" ") if isinstance(x, str) else x)
                    except Exception:
                        # If parsing fails, assume it's already an array-like or handle appropriately
                        pass

    def _generate_masks(self) -> Dict[str, torch.Tensor]:
        """
        Generate binary masks indicating presence (1) or absence (0) of spectrum data.
        Returns a dictionary mapping spectrum column name to a boolean mask tensor.
        """
        masks = {}
        for col in self.spectrum_columns:
            if col in self.df.columns:
                # Create mask: 1 if data exists (not null and not empty), 0 otherwise
                mask = self.df[col].apply(
                    lambda x: 0 if pd.isna(x) or (isinstance(x, np.ndarray) and len(x) == 0) else 1
                ).values.astype(np.float32)
                masks[col] = torch.tensor(mask, dtype=torch.float32)
            else:
                # If column doesn't exist, mask is all zeros
                masks[col] = torch.zeros(len(self.df), dtype=torch.float32)

        return masks

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """
        Retrieve a single sample.

        Returns:
            Dictionary containing:
            - 'spectra': Dict of {col_name: tensor} for available spectra
            - 'fingerprints': Tensor of fingerprint vector
            - 'conditions': Tensor of condition features (if any)
            - 'masks': Dict of {col_name: mask_tensor} indicating missing data
            - 'target': Tensor of normalized DFT energy
        """
        row = self.df.iloc[idx]

        # Extract spectra
        spectra = {}
        for col in self.spectrum_columns:
            if col in row:
                val = row[col]
                if isinstance(val, np.ndarray):
                    spectra[col] = torch.tensor(val, dtype=torch.float32)
                elif isinstance(val, list):
                    spectra[col] = torch.tensor(val, dtype=torch.float32)
                else:
                    # Handle string or other formats
                    try:
                        spectra[col] = torch.tensor(np.fromstring(str(val).strip("[]"), sep=" "), dtype=torch.float32)
                    except Exception:
                        spectra[col] = torch.zeros(1, dtype=torch.float32)  # Fallback for missing/invalid
            else:
                spectra[col] = torch.zeros(1, dtype=torch.float32)

        # Extract fingerprint
        fp_val = row[self.fingerprint_column]
        if isinstance(fp_val, np.ndarray):
            fingerprints = torch.tensor(fp_val, dtype=torch.float32)
        elif isinstance(fp_val, list):
            fingerprints = torch.tensor(fp_val, dtype=torch.float32)
        else:
            try:
                fingerprints = torch.tensor(np.fromstring(str(fp_val).strip("[]"), sep=" "), dtype=torch.float32)
            except Exception:
                fingerprints = torch.zeros(1, dtype=torch.float32)

        # Extract conditions
        conditions = torch.tensor([], dtype=torch.float32)
        if self.condition_columns:
            cond_vals = []
            for col in self.condition_columns:
                if col in row:
                    val = row[col]
                    if isinstance(val, (int, float)):
                        cond_vals.append(float(val))
                    elif isinstance(val, np.ndarray):
                        cond_vals.extend(val.tolist())
                    elif isinstance(val, list):
                        cond_vals.extend(val)
                    else:
                        try:
                            cond_vals.extend(np.fromstring(str(val).strip("[]"), sep=" ").tolist())
                        except Exception:
                            pass
            if cond_vals:
                conditions = torch.tensor(cond_vals, dtype=torch.float32)

        # Extract target
        target_val = row[self.target_column]
        if isinstance(target_val, (int, float)):
            target = torch.tensor([float(target_val)], dtype=torch.float32)
        else:
            try:
                target = torch.tensor([float(str(target_val))], dtype=torch.float32)
            except Exception:
                raise ValueError(f"Invalid target value at index {idx}: {target_val}")

        # Prepare masks
        sample_masks = {}
        if self.masks:
            for col, mask_tensor in self.masks.items():
                sample_masks[col] = mask_tensor[idx]

        return {
            "spectra": spectra,
            "fingerprints": fingerprints,
            "conditions": conditions,
            "masks": sample_masks,
            "target": target
        }


def create_dataloader(
    data_path: Union[str, Path],
    batch_size: int = 32,
    shuffle: bool = True,
    num_workers: int = 0,
    target_column: str = "normalized_dft_energy",
    spectrum_columns: List[str] = None,
    fingerprint_column: str = "ecfp4_vector",
    condition_columns: List[str] = None
):
    """
    Create a PyTorch DataLoader for the reaction dataset.

    Args:
        data_path: Path to the data file.
        batch_size: Batch size for training.
        shuffle: Whether to shuffle the data.
        num_workers: Number of worker processes for data loading.
        target_column: Target column name.
        spectrum_columns: List of spectrum column names.
        fingerprint_column: Fingerprint column name.
        condition_columns: List of condition column names.

    Returns:
        PyTorch DataLoader instance.
    """
    dataset = ReactionSample(
        data_path=data_path,
        target_column=target_column,
        spectrum_columns=spectrum_columns,
        fingerprint_column=fingerprint_column,
        condition_columns=condition_columns
    )

    return torch.utils.data.DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=True if torch.cuda.is_available() else False
    )