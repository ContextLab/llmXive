"""
Feature Assembly for Molecular Packing Efficiency Prediction.

Encodes SMILES using frozen ChemBERTa and assembles the final feature matrix
combining transformer embeddings, 3D descriptors, and confounders.
"""

import os
import sys
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any

# Import from project utils and config
from utils import fix_seed, setup_logging
from config import get_data_dir, get_models_dir, get_hf_model_path

# Configure logging
logger = logging.getLogger(__name__)

# Constants
SEED = 42
MAX_TOKENS = 128  # Maximum sequence length for ChemBERTa
DEVICE = "cpu"

def load_transformer_model(model_name: str):
    """
    Load the frozen ChemBERTa model for inference.
    Returns the tokenizer and model.
    """
    try:
        from transformers import AutoTokenizer, AutoModel
        import torch

        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name)
        model.eval()
        model.to(DEVICE)

        # Freeze parameters
        for param in model.parameters():
            param.requires_grad = False

        logger.info(f"Successfully loaded frozen model: {model_name}")
        return tokenizer, model
    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {e}")
        raise

def encode_smiles_batch(
    smiles_list: List[str],
    tokenizer,
    model,
    max_length: int = MAX_TOKENS
) -> np.ndarray:
    """
    Encode a batch of SMILES strings into fixed-length embedding vectors
    using mean pooling over token embeddings.

    Returns:
        np.ndarray: Array of shape (N, embedding_dim)
    """
    import torch
    from torch.utils.data import DataLoader, Dataset

    class SMILESDataset(Dataset):
        def __init__(self, smiles_list, tokenizer, max_length):
            self.smiles_list = smiles_list
            self.tokenizer = tokenizer
            self.max_length = max_length

        def __len__(self):
            return len(self.smiles_list)

        def __getitem__(self, idx):
            encoding = self.tokenizer(
                self.smiles_list[idx],
                return_tensors="pt",
                padding="max_length",
                truncation=True,
                max_length=self.max_length,
                add_special_tokens=True
            )
            return {
                'input_ids': encoding['input_ids'].squeeze(0),
                'attention_mask': encoding['attention_mask'].squeeze(0)
            }

    dataset = SMILESDataset(smiles_list, tokenizer, max_length)
    # Use a batch size that fits in memory (adjust if OOM)
    batch_size = 32
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

    embeddings = []

    with torch.no_grad():
        for batch in dataloader:
            input_ids = batch['input_ids'].to(DEVICE)
            attention_mask = batch['attention_mask'].to(DEVICE)

            # Get last hidden states
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            last_hidden_states = outputs.last_hidden_state

            # Mean pooling: average over the sequence length dimension (dim=1)
            # Mask out padding tokens
            input_mask_expanded = attention_mask.unsqueeze(-1).expand(
                last_hidden_states.size()
            ).float()
            sum_embeddings = torch.sum(last_hidden_states * input_mask_expanded, 1)
            sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
            mean_embeddings = sum_embeddings / sum_mask

            embeddings.append(mean_embeddings.cpu().numpy())

    return np.vstack(embeddings)

def encode_confounders_categorical(
    df: pd.DataFrame,
    column: str,
    encoder_dict: Optional[Dict[str, int]] = None,
    fit: bool = False
) -> Tuple[np.ndarray, Dict[str, int]]:
    """
    Encode a categorical column into a one-hot vector (or integer index if sparse).
    For simplicity in this assembly, we use integer encoding + scaling or one-hot.
    Given the dimensionality constraints, we will use integer encoding for now
    and let the model learn embeddings if needed, OR one-hot if few categories.
    Here we assume one-hot for small cardinality or integer for large.
    However, to keep feature matrix consistent, we'll return a 1D array per row
    for each confounder, and the caller concatenates them.

    Actually, for the feature matrix, we need a fixed number of columns.
    Let's do one-hot for Lattice System (small), and integer for others.
    But to simplify, let's just return the encoded values as a list of columns.
    We will handle this in the main assembly function.
    """
    # Placeholder: Logic moved to main assembly for clarity
    pass

def assemble_features(
    df: pd.DataFrame,
    tokenizer,
    model
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Assemble the final feature matrix and target vector.

    Features:
    1. SMILES Transformer Embedding (mean pooled)
    2. 3D Descriptors: radius_of_gyration, asphericity, principal_moments (3 values)
    3. Confounders:
       - lattice_system (One-hot encoded)
       - temperature_K (Normalized/Standardized)
       - has_solvent (Binary)

    Target: CAPE (Composition-Adjusted Packing Efficiency)

    Returns:
        Tuple[np.ndarray, np.ndarray]: (feature_matrix, targets)
    """
    logger.info("Starting feature assembly...")

    # 1. Extract SMILES and encode
    smiles_list = df['smiles'].tolist()
    logger.info(f"Encoding {len(smiles_list)} SMILES strings...")
    try:
        smiles_embeddings = encode_smiles_batch(smiles_list, tokenizer, model)
        logger.info(f"SMILES embeddings shape: {smiles_embeddings.shape}")
    except Exception as e:
        logger.error(f"Failed to encode SMILES: {e}")
        raise

    # 2. Extract 3D Descriptors
    # Columns: radius_of_gyration, asphericity, principal_moments (3 floats)
    desc_cols = ['radius_of_gyration', 'asphericity', 'principal_moments']
    # principal_moments is stored as a list/array in the CSV, need to explode or parse
    # Assuming it's stored as a string representation of a list or a JSON string
    # Let's handle it safely.
    def parse_moments(val):
        if isinstance(val, (list, np.ndarray)):
            return list(val)
        if isinstance(val, str):
            # Remove brackets and split
            val = val.strip('[]')
            if not val:
                return [0.0, 0.0, 0.0]
            parts = val.split(',')
            return [float(p.strip()) for p in parts]
        return [0.0, 0.0, 0.0]

    moments_list = df['principal_moments'].apply(parse_moments).tolist()
    moments_array = np.array(moments_list)  # Shape (N, 3)

    radius_gyration = df['radius_of_gyration'].values.reshape(-1, 1)
    asphericity = df['asphericity'].values.reshape(-1, 1)

    descriptors = np.hstack([radius_gyration, asphericity, moments_array])
    logger.info(f"Descriptors shape: {descriptors.shape}")

    # 3. Encode Confounders
    # Lattice System: One-hot
    lattice_systems = df['lattice_system'].unique().tolist()
    lattice_map = {s: i for i, s in enumerate(lattice_systems)}
    n_lattice = len(lattice_systems)

    lattice_one_hot = np.zeros((len(df), n_lattice))
    for i, ls in enumerate(df['lattice_system']):
        if ls in lattice_map:
            lattice_one_hot[i, lattice_map[ls]] = 1.0

    # Temperature: Normalize (StandardScaler logic manually for reproducibility)
    # We compute mean/std on the training set (which is the whole set here for assembly)
    temps = df['temperature_K'].values.astype(float)
    temp_mean = temps.mean()
    temp_std = temps.std()
    if temp_std == 0:
        temp_std = 1.0
    temps_normalized = (temps - temp_mean) / temp_std
    temps_normalized = temps_normalized.reshape(-1, 1)

    # Has Solvent: Binary
    has_solvent = df['has_solvent'].astype(int).values.reshape(-1, 1)

    # Concatenate all features
    # [SMILES_Embed] [Radius] [Asphericity] [Moments_3] [Lattice_OneHot] [Temp] [Solvent]
    feature_matrix = np.hstack([
        smiles_embeddings,
        descriptors,
        lattice_one_hot,
        temps_normalized,
        has_solvent
    ])

    # 4. Extract Target (CAPE)
    targets = df['cape'].values.astype(float)

    logger.info(f"Final feature matrix shape: {feature_matrix.shape}")
    logger.info(f"Target vector shape: {targets.shape}")

    return feature_matrix, targets

def main():
    """
    Main entry point for feature assembly.
    Reads data/dataset.csv, processes, and saves data/features_matrix.npy and data/targets.npy.
    """
    fix_seed(SEED)
    setup_logging()

    # Paths
    data_dir = get_data_dir()
    input_path = os.path.join(data_dir, "dataset.csv")
    features_path = os.path.join(data_dir, "features_matrix.npy")
    targets_path = os.path.join(data_dir, "targets.npy")

    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    # Load dataset
    logger.info(f"Loading dataset from {input_path}")
    df = pd.read_csv(input_path)

    # Validate required columns
    required_cols = [
        'smiles', 'radius_of_gyration', 'asphericity', 'principal_moments',
        'lattice_system', 'temperature_K', 'has_solvent', 'cape'
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        sys.exit(1)

    # Load model
    model_name = get_hf_model_path()
    if not model_name:
        model_name = "seyonec/ChemBERTa-zinc-base-v1"
    
    logger.info(f"Loading transformer model: {model_name}")
    tokenizer, model = load_transformer_model(model_name)

    # Assemble features
    feature_matrix, targets = assemble_features(df, tokenizer, model)

    # Save outputs
    logger.info(f"Saving feature matrix to {features_path}")
    np.save(features_path, feature_matrix)

    logger.info(f"Saving targets to {targets_path}")
    np.save(targets_path, targets)

    logger.info("Feature assembly completed successfully.")

if __name__ == "__main__":
    main()