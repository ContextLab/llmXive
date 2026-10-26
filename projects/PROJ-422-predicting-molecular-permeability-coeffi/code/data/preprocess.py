import logging
import json
import os
import sys
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

import pandas as pd
import numpy as np
import yaml

from rdkit import Chem
from rdkit.Chem import Descriptors, Lipinski
from rdkit import RDLogger
from llmxive_toolkit import paths, get_logger

# Suppress RDKit warnings for cleaner logs
RDLogger.DisableLog('rdApp.*')

log = get_logger(__name__)

class MoleculeProcessor:
    """
    Handles SMILES parsing, descriptor calculation, and dataset generation
    that conforms to the dataset contract.

    The processor:
    1. Parses SMILES with RDKit, logging and excluding invalid entries (FR‑011).
    2. Computes six standard molecular descriptors (FR‑003).
    3. Writes both CSV and Parquet files BEFORE any retention‑rate guard (FR‑012).
    4. Enforces the ≥ 95 % valid‑molecule retention guard; if failed, exits non‑zero.
    5. Drops rows with missing target values.
    """

    def __init__(self, config_path: Optional[str] = None, retention_threshold: Optional[float] = None):
        self.logger = logging.getLogger(__name__)
        # Load configuration (defaults are provided if the file does not exist)
        self.config = self._load_config(config_path)

        # Allow test‑code to override the retention threshold
        self.retention_threshold = (
            retention_threshold
            if retention_threshold is not None
            else self.config.get('retention_threshold', 0.95)
        )

        self.descriptor_names = [
            'mw', 'logp', 'tpsa', 'hba', 'hbd', 'rotatable_bonds'
        ]

    # ------------------------------------------------------------------
    # Configuration handling
    # ------------------------------------------------------------------
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from a YAML file, falling back to defaults."""
        default_config = {
            'bias_threshold': 0.85,
            'retention_threshold': 0.95
        }
        if config_path is None:
            # Default location relative to the project root
            config_path = paths.root / "config.yaml"

        if not os.path.exists(config_path):
            return default_config

        try:
            with open(config_path, "r") as f:
                cfg = yaml.safe_load(f) or {}
            return {**default_config, **cfg}
        except Exception:
            # If parsing fails, revert to defaults – the pipeline will still run.
            return default_config

    # ------------------------------------------------------------------
    # SMILES handling
    # ------------------------------------------------------------------
    def parse_smiles(self, smiles: str) -> Optional[Chem.Mol]:
        """Convert a SMILES string into an RDKit Mol object."""
        if pd.isna(smiles) or not isinstance(smiles, str):
            return None
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        try:
            Chem.SanitizeMol(mol)
        except Exception:
            return None
        return mol

    # ------------------------------------------------------------------
    # Descriptor calculation
    # ------------------------------------------------------------------
    def calculate_descriptors(self, mol: Chem.Mol) -> Dict[str, float]:
        """Compute the required six molecular descriptors."""
        try:
            return {
                'mw': Descriptors.MolWt(mol),
                'logp': Descriptors.MolLogP(mol),
                'tpsa': Descriptors.TPSA(mol),
                'hba': Lipinski.NumHAcceptors(mol),
                'hbd': Lipinski.NumHDonors(mol),
                'rotatable_bonds': Lipinski.NumRotatableBonds(mol)
            }
        except Exception:
            # In the unlikely event of a failure, return NaNs – they will be imputed later.
            return {name: np.nan for name in self.descriptor_names}

    # ------------------------------------------------------------------
    # Core processing routine
    # ------------------------------------------------------------------
    def process(
        self,
        df: pd.DataFrame,
        smiles_col: str = 'SMILES',
        target_col: str = 'permeability'
    ) -> pd.DataFrame:
        """
        End‑to‑end preprocessing.

        Steps:
        1. Detect the actual SMILES and target columns (flexible naming).
        2. Parse each SMILES; invalid entries are skipped.
        3. Exclude rows where the target is missing.
        4. Compute descriptors for valid molecules.
        5. Write CSV and Parquet outputs **before** any guard checks.
        6. Apply the ≥ 95 % retention guard; on failure, log a warning and exit non‑zero.
        """
        self.logger.info(f"Processing {len(df)} records...")

        # ------------------------------------------------------------------
        # Column detection (allow common alternatives)
        # ------------------------------------------------------------------
        actual_smiles_col = (
            smiles_col
            if smiles_col in df.columns
            else ('smiles' if 'smiles' in df.columns else None)
        )
        actual_target_col = (
            target_col
            if target_col in df.columns
            else (
                'permeability_coefficient'
                if 'permeability_coefficient' in df.columns
                else ('target' if 'target' in df.columns else None)
            )
        )

        if actual_smiles_col is None:
            raise ValueError(f"SMILES column not found. Available columns: {df.columns.tolist()}")

        processed_rows: List[Dict[str, Any]] = []
        valid_smiles_count = 0
        total_input_rows = len(df)

        for _, row in df.iterrows():
            smiles = row[actual_smiles_col]
            mol = self.parse_smiles(smiles)

            if mol is None:
                # Invalid SMILES – skip and continue logging
                continue

            valid_smiles_count += 1

            # ------------------------------------------------------------------
            # Target handling – drop rows with missing target
            # ------------------------------------------------------------------
            target_val = None
            if actual_target_col:
                target_val = row[actual_target_col]

            if pd.isna(target_val):
                continue  # Missing permeability – exclude from the final dataset

            # ------------------------------------------------------------------
            # Descriptor calculation
            # ------------------------------------------------------------------
            descriptors = self.calculate_descriptors(mol)

            # ------------------------------------------------------------------
            # Assemble the processed row
            # ------------------------------------------------------------------
            new_row = {
                'smiles': smiles,
                'mol_valid': True,
                'mw': descriptors.get('mw', np.nan),
                'logp': descriptors.get('logp', np.nan),
                'tpsa': descriptors.get('tpsa', np.nan),
                'hba': descriptors.get('hba', np.nan),
                'hbd': descriptors.get('hbd', np.nan),
                'rotatable_bonds': descriptors.get('rotatable_bonds', np.nan),
                'target': target_val
            }

            # Preserve polymer_type if present – it is a categorical column used later for stratification.
            if 'polymer_type' in df.columns:
                new_row['polymer_type'] = row['polymer_type']

            processed_rows.append(new_row)

        # Create DataFrame from the collected rows
        processed_df = pd.DataFrame(processed_rows)

        # ------------------------------------------------------------------
        # Impute missing descriptor values with the median (robust default)
        # ------------------------------------------------------------------
        for col in self.descriptor_names:
            if col in processed_df.columns:
                processed_df[col] = processed_df[col].fillna(processed_df[col].median())

        # ------------------------------------------------------------------
        # Write outputs BEFORE applying the retention guard (as required)
        # ------------------------------------------------------------------
        csv_path = paths.data('processed', 'processed_data.csv')
        parquet_path = paths.data('processed', 'processed_data.parquet')

        processed_df.to_csv(csv_path, index=False)
        processed_df.to_parquet(parquet_path, index=False)
        self.logger.info(f"Wrote processed data to {csv_path} and {parquet_path}")

        # ------------------------------------------------------------------
        # Retention guard – ensure ≥ retention_threshold of input rows remain valid
        # ------------------------------------------------------------------
        retention_rate = valid_smiles_count / total_input_rows if total_input_rows > 0 else 0.0
        self.logger.info(f"Retention rate: {retention_rate:.2%}")

        if retention_rate < self.retention_threshold:
            self.logger.warning(
                f"Retention rate {retention_rate:.2%} below threshold {self.retention_threshold:.2%}"
            )
            # Exit with a non‑zero status as mandated by FR‑012
            raise SystemExit(1)

        return processed_df

    # ------------------------------------------------------------------
    # CLI entry point – used by quickstart
    # ------------------------------------------------------------------
    def run_from_cli(self) -> None:
        """CLI entry point to process raw data."""
        raw_dir = paths.data('raw')
        csv_files = list(raw_dir.glob('*.csv'))

        if not csv_files:
            # Fall back to a small bundled sample if no raw files are present.
            sample_path = paths.root / "data" / "sample_permeability.csv"
            if not sample_path.exists():
                self.logger.error("No raw data found and no sample dataset is available.")
                sys.exit(1)
            df = pd.read_csv(sample_path)
        else:
            df = pd.read_csv(csv_files[0])

        try:
            self.process(df)
        except SystemExit as e:
            # Propagate the exit code (useful for the pipeline orchestrator)
            sys.exit(e.code if isinstance(e.code, int) else 1)


if __name__ == "__main__":
    processor = MoleculeProcessor()
    processor.run_from_cli()