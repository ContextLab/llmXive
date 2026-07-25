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
    PyTorch Dataset for Reaction Samples.
    
    Handles:
    - Spectral data (IR/Raman, NMR) with variable lengths/channels.
    - Molecular fingerprints (ECFP4).
    - Reaction conditions (one-hot/embeddings).
    - Target variable: Normalized DFT total molecular energy.
    
    Implements masking for missing channels as required by the task.
    """
    
    def __init__(
        self,
        data_path: Union[str, Path],
        target_column: str = "normalized_dft_energy",
        missing_channels: Optional[List[str]] = None,
        mask_value: float = 0.0
    ):
        """
        Initialize the ReactionSample dataset.
        
        Args:
            data_path: Path to the processed parquet/csv file containing split data.
                       Expected schema includes spectral columns, fingerprint columns, 
                       condition columns, and the target column.
            target_column: Name of the column containing the target variable 
                           (normalized DFT total molecular energy).
            missing_channels: List of channel names to treat as missing/masked.
                              Expected values: 'ir', 'raman', 'nmr'.
            mask_value: Value to fill masked spectral data with.
        """
        self.data_path = Path(data_path)
        self.target_column = target_column
        self.missing_channels = missing_channels or []
        self.mask_value = mask_value
        
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_path}")
        
        logger.info(f"Loading dataset from {self.data_path}")
        # Load data
        if self.data_path.suffix == '.parquet':
            self.df = pd.read_parquet(self.data_path)
        elif self.data_path.suffix == '.csv':
            self.df = pd.read_csv(self.data_path)
        else:
            raise ValueError(f"Unsupported file format: {self.data_path.suffix}")
        
        logger.info(f"Loaded {len(self.df)} samples")
        
        # Validate target column exists
        if self.target_column not in self.df.columns:
            raise ValueError(f"Target column '{self.target_column}' not found in data. "
                             f"Available columns: {list(self.df.columns)}")
        
        # Identify spectral, fingerprint, and condition columns dynamically
        # This assumes standard naming conventions established in preprocessing
        self.spectral_cols = [col for col in self.df.columns if col.startswith(('ir_', 'raman_', 'nmr_'))]
        self.fp_cols = [col for col in self.df.columns if col.startswith('fp_')]
        self.cond_cols = [col for col in self.df.columns if col.startswith('cond_')]
        
        if not self.fp_cols:
            logger.warning("No fingerprint columns found in data.")
        if not self.cond_cols:
            logger.warning("No condition columns found in data.")
            
    def __len__(self) -> int:
        return len(self.df)
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """
        Retrieve a single sample.
        
        Returns a dictionary with:
        - 'spectra': Concatenated spectral tensor (masked if necessary)
        - 'fingerprints': Fingerprint vector
        - 'conditions': Condition vector
        - 'target': Normalized DFT energy
        - 'mask': Boolean mask indicating which spectral channels are valid
        """
        row = self.df.iloc[idx]
        
        # Extract target
        target = float(row[self.target_column])
        
        # Extract Fingerprints
        fp_vec = np.zeros(len(self.fp_cols))
        for i, col in enumerate(self.fp_cols):
            fp_vec[i] = row[col]
        fp_tensor = torch.tensor(fp_vec, dtype=torch.float32)
        
        # Extract Conditions
        cond_vec = np.zeros(len(self.cond_cols))
        for i, col in enumerate(self.cond_cols):
            cond_vec[i] = row[col]
        cond_tensor = torch.tensor(cond_vec, dtype=torch.float32)
        
        # Extract and Process Spectra
        # We expect spectral data to be stored as arrays or lists in the dataframe
        # or as fixed-length columns. Assuming fixed-length columns for simplicity 
        # based on T014 preprocessing output.
        
        # Determine spectral dimensions
        # We assume a fixed grid size per channel type as defined in T014
        # If the dataframe stores flattened spectra, we need to know the lengths.
        # For robustness, we check if columns are present and handle missing channels.
        
        ir_data = np.zeros(0)
        raman_data = np.zeros(0)
        nmr_data = np.zeros(0)
        
        # Helper to extract and pad/resize if necessary (assuming fixed grid in T014)
        def get_channel_data(prefix: str, channel_name: str) -> np.ndarray:
            cols = [c for c in self.df.columns if c.startswith(f"{prefix}_")]
            if not cols:
                return np.array([])
            
            # Assuming all columns for this prefix exist and are ordered
            # In a real scenario, we might need to reconstruct the array from a list column
            # or sort columns numerically. Here we assume sorted column names like 'ir_0', 'ir_1'
            # or 'ir_wavenumber_1000', etc.
            # To be safe, we extract the values in column order.
            vals = [row[c] for c in sorted(cols)]
            
            # Handle potential NaNs from missing data in the row
            vals = [0.0 if pd.isna(v) else float(v) for v in vals]
            return np.array(vals)

        # Check for missing channels and apply masking
        if 'ir' in self.missing_channels:
            ir_data = np.full(len(get_channel_data('ir', 'ir')), self.mask_value)
            ir_mask = False
        else:
            ir_data = get_channel_data('ir', 'ir')
            ir_mask = True if len(ir_data) > 0 else False
            # If data is missing entirely (not just masked), fill with mask_value
            if len(ir_data) == 0:
                ir_data = np.array([self.mask_value])
                ir_mask = False

        if 'raman' in self.missing_channels:
            raman_data = np.full(len(get_channel_data('raman', 'raman')), self.mask_value)
            raman_mask = False
        else:
            raman_data = get_channel_data('raman', 'raman')
            raman_mask = True if len(raman_data) > 0 else False
            if len(raman_data) == 0:
                raman_data = np.array([self.mask_value])
                raman_mask = False

        if 'nmr' in self.missing_channels:
            nmr_data = np.full(len(get_channel_data('nmr', 'nmr')), self.mask_value)
            nmr_mask = False
        else:
            nmr_data = get_channel_data('nmr', 'nmr')
            nmr_mask = True if len(nmr_data) > 0 else False
            if len(nmr_data) == 0:
                nmr_data = np.array([self.mask_value])
                nmr_mask = False

        # Concatenate spectra into a single tensor
        # Shape: (num_channels, max_length) or flattened? 
        # The model (T024) expects a specific input shape. 
        # We will stack them as (3, max_len) or pad to max_len.
        
        max_len = max(len(ir_data), len(raman_data), len(nmr_data))
        
        def pad_to_max(arr: np.ndarray, max_l: int) -> np.ndarray:
            if len(arr) == 0:
                return np.full(max_l, self.mask_value)
            if len(arr) < max_l:
                return np.pad(arr, (0, max_l - len(arr)), mode='constant', constant_values=self.mask_value)
            return arr[:max_l]

        ir_padded = pad_to_max(ir_data, max_len)
        raman_padded = pad_to_max(raman_data, max_len)
        nmr_padded = pad_to_max(nmr_data, max_len)
        
        spectra_stack = np.stack([ir_padded, raman_padded, nmr_padded])
        spectra_tensor = torch.tensor(spectra_stack, dtype=torch.float32)
        
        # Create a mask tensor indicating valid channels (1.0 for valid, 0.0 for masked)
        # Shape: (3,) corresponding to [IR, Raman, NMR]
        channel_mask = torch.tensor([
            1.0 if ir_mask else 0.0,
            1.0 if raman_mask else 0.0,
            1.0 if nmr_mask else 0.0
        ], dtype=torch.float32)

        return {
            'spectra': spectra_tensor,
            'fingerprints': fp_tensor,
            'conditions': cond_tensor,
            'target': torch.tensor(target, dtype=torch.float32),
            'mask': channel_mask,
            'index': idx
        }

def create_dataloader(
    data_path: Union[str, Path],
    batch_size: int = 32,
    shuffle: bool = True,
    missing_channels: Optional[List[str]] = None,
    num_workers: int = 0
) -> torch.utils.data.DataLoader:
    """
    Create a PyTorch DataLoader for the ReactionSample dataset.
    
    Args:
        data_path: Path to the processed data file.
        batch_size: Batch size for training/evaluation.
        shuffle: Whether to shuffle the dataset.
        missing_channels: List of channels to mask.
        num_workers: Number of workers for data loading.
        
    Returns:
        A PyTorch DataLoader instance.
    """
    dataset = ReactionSample(
        data_path=data_path,
        missing_channels=missing_channels
    )
    
    return torch.utils.data.DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=True if torch.cuda.is_available() else False,
        collate_fn=_collate_fn
    )

def _collate_fn(batch: List[Dict[str, torch.Tensor]]) -> Dict[str, torch.Tensor]:
    """
    Custom collate function to handle variable lengths if necessary.
    Currently assumes fixed lengths from preprocessing, so standard stacking works.
    """
    spectra = torch.stack([item['spectra'] for item in batch])
    fingerprints = torch.stack([item['fingerprints'] for item in batch])
    conditions = torch.stack([item['conditions'] for item in batch])
    targets = torch.stack([item['target'] for item in batch])
    masks = torch.stack([item['mask'] for item in batch])
    indices = torch.tensor([item['index'] for item in batch])
    
    return {
        'spectra': spectra,
        'fingerprints': fingerprints,
        'conditions': conditions,
        'target': targets,
        'mask': masks,
        'index': indices
    }
