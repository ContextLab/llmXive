"""Feature extraction and preprocessing module."""
from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

from src.modeling.config import load_config
from src.utils.logging import setup_logger, get_logger, log_operation
from src.utils.state_manager import register_artifact

_logger: Optional[Any] = None


def _ensure_logger() -> Any:
    global _logger
    if _logger is None:
        _logger = setup_logger("preprocessing")
    return _logger


def compute_file_checksum(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096)):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def extract_features_from_smiles(smiles: str) -> Optional[Dict[str, float]]:
    """Extract molecular features from a SMILES string.

    Features:
      - Molecular weight
      - Atom counts (C, N, O, S, P, halogens)
      - Bond counts
      - Topological indices
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None

        features = {}

        # Molecular weight
        features["molecular_weight"] = Descriptors.MolWt(mol)

        # Atom counts
        features["num_atoms"] = mol.GetNumAtoms()
        features["num_bonds"] = mol.GetNumBonds()
        features["num_heavy_atoms"] = mol.GetNumHeavyAtoms()

        # Element counts
        for atom in mol.GetAtoms():
            symbol = atom.GetSymbol()
            key = f"num_{symbol.lower()}"
            features[key] = features.get(key, 0) + 1

        # Topological indices
        features["num_rotatable_bonds"] = rdMolDescriptors.CalcNumRotatableBonds(mol)
        features["num_h_acceptors"] = rdMolDescriptors.CalcNumHBA(mol)
        features["num_h_donors"] = rdMolDescriptors.CalcNumHBD(mol)
        features["tpsa"] = Descriptors.TPSA(mol)
        features["logp"] = Descriptors.MolLogP(mol)

        return features
    except Exception as e:
        _logger = _ensure_logger()
        _logger.log("feature_extraction_error", smiles=smiles, error=str(e))
        return None


def preprocess_batch(
    df: pd.DataFrame,
    smiles_column: str = "reactants_smiles",
    batch_size: int = 1000,
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """Process a batch of SMILES strings and extract features.

    Returns:
        Tuple of (DataFrame with features, list of errors)
    """
    _logger = _ensure_logger()
    errors = []
    all_features = []

    for idx, row in df.iterrows():
        smiles = row.get(smiles_column)
        if not smiles:
            errors.append({"index": idx, "reason": "missing_smiles"})
            continue

        features = extract_features_from_smiles(smiles)
        if features is None:
            errors.append({"index": idx, "reason": "invalid_smiles", "smiles": smiles})
            continue

        all_features.append(features)

    if not all_features:
        return pd.DataFrame(), errors

    # Create feature DataFrame
    feature_df = pd.DataFrame(all_features)

    # Align with original index
    feature_df.index = df.index[: len(feature_df)]

    # Merge with original data
    result_df = pd.concat([df.iloc[: len(feature_df)], feature_df], axis=1)

    return result_df, errors


def apply_dimensionality_reduction(
    feature_df: pd.DataFrame,
    k: int = 100,
) -> Tuple[pd.DataFrame, Any]:
    """Apply dimensionality reduction (Variance Threshold + SelectKBest).

    Returns:
        Tuple of (reduced feature DataFrame, fitted selector)
    """
    _logger = _ensure_logger()

    # Select numeric columns
    numeric_cols = feature_df.select_dtypes(include=[np.number]).columns.tolist()
    X = feature_df[numeric_cols].fillna(0)

    if X.shape[1] == 0:
        _logger.log("no_numeric_features")
        return feature_df, None

    # Apply SelectKBest
    selector = SelectKBest(score_func=f_regression, k=min(k, X.shape[1]))
    X_selected = selector.fit_transform(X)

    # Get selected feature names
    mask = selector.get_support()
    selected_cols = [col for col, keep in zip(numeric_cols, mask) if keep]

    # Create reduced DataFrame
    reduced_df = pd.DataFrame(X_selected, columns=selected_cols, index=feature_df.index)

    _logger.log(
        "dimensionality_reduction_complete",
        original_features=len(numeric_cols),
        selected_features=len(selected_cols),
    )

    return reduced_df, selector


def save_feature_matrix(
    df: pd.DataFrame,
    output_path: str,
    selector: Optional[Any] = None,
) -> None:
    """Save feature matrix to parquet with checksum and metadata."""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save to parquet
    df.to_parquet(output_path, index=False)

    # Compute checksum
    checksum = compute_file_checksum(output_path)

    # Save metadata
    metadata = {
        "timestamp": pd.Timestamp.utcnow().isoformat(),
        "checksum": checksum,
        "shape": list(df.shape),
        "columns": df.columns.tolist(),
    }
    if selector is not None:
        metadata["selected_features"] = selector.get_support().tolist()

    metadata_path = f"{output_path}.metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    register_artifact(output_path, checksum)


def load_feature_matrix(input_path: str) -> pd.DataFrame:
    """Load feature matrix from parquet file."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Feature matrix not found: {input_path}")
    return pd.read_parquet(input_path)


def preprocess_and_save_features(
    input_path: str,
    output_path: str,
    k_features: int = 100,
) -> None:
    """Main preprocessing pipeline.

    1. Load raw reaction data
    2. Extract features from SMILES
    3. Apply dimensionality reduction
    4. Save feature matrix
    """
    _logger = _ensure_logger()

    # Load input data
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)
    _logger.log("input_loaded", rows=len(df), path=input_path)

    # Extract features
    processed_df, errors = preprocess_batch(df)

    if processed_df.empty:
        _logger.log("no_features_extracted")
        # Create empty output
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame().to_parquet(output_path, index=False)
        return

    # Apply dimensionality reduction
    reduced_df, selector = apply_dimensionality_reduction(processed_df, k=k_features)

    # Save feature matrix
    save_feature_matrix(reduced_df, output_path, selector)

    # Log errors
    if errors:
        error_log_path = str(Path(output_path).parent / "preprocessing_errors.json")
        with open(error_log_path, "w") as f:
            json.dump(errors, f, indent=2)

    _logger.log(
        "preprocessing_complete",
        input_rows=len(df),
        output_rows=len(reduced_df),
        output_path=output_path,
    )


def main() -> None:
    """Main entry point for preprocessing script."""
    import argparse

    parser = argparse.ArgumentParser(description="Preprocess reaction data")
    parser.add_argument(
        "--input",
        required=True,
        help="Input CSV file path",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output feature matrix parquet path",
    )
    parser.add_argument(
        "--k-features",
        type=int,
        default=100,
        help="Number of features to select",
    )

    args = parser.parse_args()

    # Initialize logger
    setup_logger("preprocessing")

    try:
        preprocess_and_save_features(
            args.input,
            args.output,
            k_features=args.k_features,
        )
    except Exception as e:
        _logger = _ensure_logger()
        _logger.log("preprocessing_failed", error=str(e))
        raise


if __name__ == "__main__":
    main()
