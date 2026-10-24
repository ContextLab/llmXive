import logging
import json
import os
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

import pandas as pd
import numpy as np
import yaml

from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors, Lipinski
from rdkit import RDLogger
from llmxive_toolkit import paths, get_logger

# Suppress RDKit warnings for cleaner logs
RDLogger.DisableLog('rdApp.*')

log = get_logger(__name__)

class MoleculeProcessor:
    """
    Handles SMILES parsing, descriptor calculation, graph feature extraction,
    bias checking, and final dataset generation that conforms to the
    contract defined in `specs/.../contracts/dataset.schema.yaml`.
    """

    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)
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
            # Default location (relative to project root)
            config_path = os.path.join(
                "projects",
                "PROJ-422-predicting-molecular-permeability-coeffi",
                "config.yaml"
            )

        if not os.path.exists(config_path):
            self.logger.warning(
                f"Config file not found at {config_path}, using defaults."
            )
            return default_config

        with open(config_path, "r") as f:
            cfg = yaml.safe_load(f) or {}
        return {
            'bias_threshold': cfg.get('bias_threshold', default_config['bias_threshold']),
            'retention_threshold': cfg.get('retention_threshold', default_config['retention_threshold'])
        }

    # ------------------------------------------------------------------
    # SMILES parsing
    # ------------------------------------------------------------------
    def parse_smiles(self, smiles: str) -> Optional[Chem.Mol]:
        """
        Convert a SMILES string into an RDKit Mol object.
        Returns None if parsing or sanitisation fails.
        """
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            self.logger.warning(f"Invalid SMILES (cannot parse): {smiles}")
            return None
        try:
            Chem.SanitizeMol(mol)
        except Exception:
            self.logger.warning(f"Invalid SMILES (sanitisation failed): {smiles}")
            return None
        return mol

    # ------------------------------------------------------------------
    # Descriptor calculation (lower‑case keys matching the schema)
    # ------------------------------------------------------------------
    def calculate_descriptors(self, mol: Chem.Mol) -> Dict[str, float]:
        """
        Compute the required set of molecular descriptors.
        Keys are lower‑case to match the dataset contract.
        """
        try:
            return {
                'mw': Descriptors.MolWt(mol),
                'logp': Descriptors.MolLogP(mol),
                'tpsa': Descriptors.TPSA(mol),
                'hba': Lipinski.NumHAcceptors(mol),
                'hbd': Lipinski.NumHDonors(mol),
                'rotatable_bonds': Lipinski.NumRotatableBonds(mol)
            }
        except Exception as e:
            self.logger.warning(f"Descriptor calculation failed: {e}")
            return {}

    # ------------------------------------------------------------------
    # Graph feature extraction (JSON strings for node/edge features)
    # ------------------------------------------------------------------
    def calculate_graph_json(self, mol: Chem.Mol) -> Tuple[str, str]:
        """
        Produce JSON strings representing node and edge features.
        The JSON format is a list of dictionaries; each dictionary
        contains a small set of chemically relevant attributes.
        """
        # Node features
        node_list = []
        for idx, atom in enumerate(mol.GetAtoms()):
            node_feat = {
                'atom_idx': idx,
                'symbol': atom.GetSymbol(),
                'atomic_num': atom.GetAtomicNum(),
                'degree': atom.GetDegree(),
                'formal_charge': atom.GetFormalCharge(),
                'hybridization': str(atom.GetHybridization()),
                'aromatic': atom.GetIsAromatic()
            }
            node_list.append(node_feat)

        # Edge features
        edge_list = []
        for bond in mol.GetBonds():
            edge_feat = {
                'start': bond.GetBeginAtomIdx(),
                'end': bond.GetEndAtomIdx(),
                'bond_type': str(bond.GetBondType()),
                'aromatic': bond.GetIsAromatic()
            }
            edge_list.append(edge_feat)

        node_json = json.dumps(node_list)
        edge_json = json.dumps(edge_list)
        return node_json, edge_json

    # ------------------------------------------------------------------
    # Bias check (FR‑013)
    # ------------------------------------------------------------------
    def _check_bias(self, df: pd.DataFrame, target_col: str) -> None:
        """
        Compute Pearson correlation between each standard descriptor and the
        target. If any absolute correlation exceeds the configured threshold,
        a warning is logged and a ``bias_warning`` flag is added to the
        dataframe.
        """
        self.logger.info("Performing bias check (FR‑013)...")
        descriptor_cols = [col for col in self.descriptor_names if col in df.columns]

        if not descriptor_cols:
            self.logger.warning("No descriptor columns found for bias check.")
            return

        if target_col not in df.columns:
            self.logger.warning(f"Target column '{target_col}' missing; skipping bias check.")
            return

        high_corr = []
        for col in descriptor_cols:
            corr = df[[col, target_col]].corr().iloc[0, 1]
            if abs(corr) > self.config.get('bias_threshold', 0.85):
                high_corr.append((col, corr))
                self.logger.warning(f"HIGH CORRELATION: {col} vs {target_col} = {corr:.4f}")

        if high_corr:
            df['bias_warning'] = 'potentially confounded'
            self.logger.warning(
                f"Bias warning triggered. High correlations: {high_corr}"
            )
        else:
            df['bias_warning'] = None
            self.logger.info("Bias check passed; no high correlations detected.")

    # ------------------------------------------------------------------
    # Core processing routine required by the task (process)
    # ------------------------------------------------------------------
    def process(
        self,
        df: pd.DataFrame,
        smiles_col: str = 'SMILES',
        target_col: str = 'permeability_coefficient'
    ) -> pd.DataFrame:
        """
        End‑to‑end preprocessing according to T002 specifications.

        Steps performed:
          1. Parse SMILES, dropping rows that cannot be parsed.
          2. Compute the required descriptor set.
          3. Build JSON columns ``node_features`` and ``edge_features``.
          4. Exclude rows where the target column is missing or NaN (with a warning).
          5. Median‑impute any missing descriptor values.
          6. Perform the FR‑011 retention check and FR‑013 bias check.
          7. Write both ``processed_data.csv`` and ``processed_data.parquet`` before any guard.
          8. Return the processed ``pd.DataFrame``.
        """
        self.logger.info(f"Starting preprocessing of {len(df)} records...")

        processed_rows: List[Dict[str, Any]] = []
        invalid_smiles = 0
        valid_smiles = 0  # counts rows where SMILES could be parsed (mol_valid)

        for _, row in df.iterrows():
            smiles = row.get(smiles_col)
            if pd.isna(smiles):
                invalid_smiles += 1
                self.logger.warning("Missing SMILES value; row excluded.")
                continue

            mol = self.parse_smiles(smiles)
            if mol is None:
                invalid_smiles += 1
                continue

            # SMILES successfully parsed
            valid_smiles += 1

            # Descriptors
            descriptors = self.calculate_descriptors(mol)
            if not descriptors:
                # Treat as invalid molecule for safety.
                invalid_smiles += 1
                continue

            # Graph JSON
            node_json, edge_json = self.calculate_graph_json(mol)

            # Target handling
            target_val = row.get(target_col)
            if pd.isna(target_val):
                self.logger.warning(
                    f"Row with SMILES {smiles} missing target '{target_col}'; excluded."
                )
                continue

            # Assemble row respecting the contract schema
            new_row = {
                'smiles': smiles,
                'mol_valid': True,
                'mw': descriptors['mw'],
                'logp': descriptors['logp'],
                'tpsa': descriptors['tpsa'],
                'hba': descriptors['hba'],
                'hbd': descriptors['hbd'],
                'rotatable_bonds': descriptors['rotatable_bonds'],
                'target': target_val,
                'node_features': node_json,
                'edge_features': edge_json
            }

            # Preserve optional polymer_type if present in the source dataframe
            if 'polymer_type' in df.columns:
                new_row['polymer_type'] = row['polymer_type']

            processed_rows.append(new_row)

        total_rows = len(df)
        retention_rate = valid_smiles / total_rows if total_rows > 0 else 0.0

        self.logger.info(f"Valid molecules after SMILES parsing: {valid_smiles}")
        self.logger.info(f"Invalid SMILES count: {invalid_smiles}")
        self.logger.info(f"Retention rate (mol_valid / total): {retention_rate:.2%}")

        # Create DataFrame from rows that have a target
        processed_df = pd.DataFrame(processed_rows)

        # Median imputation for descriptor columns (if any NaNs slipped through)
        for col in self.descriptor_names:
            if col in processed_df.columns:
                median_val = processed_df[col].median()
                processed_df[col].fillna(median_val, inplace=True)

        # Bias check (FR‑013)
        self._check_bias(processed_df, target_col='target')

        # ------------------------------------------------------------------
        # Write outputs BEFORE any retention guard (per specification)
        # ------------------------------------------------------------------
        csv_path = paths.data('processed', 'processed_data.csv')
        parquet_path = paths.data('processed', 'processed_data.parquet')

        processed_df.to_csv(csv_path, index=False)
        self.logger.info(f"Processed CSV written to {csv_path}")

        # Write Parquet; requires pyarrow (declared in requirements.txt)
        processed_df.to_parquet(parquet_path, index=False)
        self.logger.info(f"Processed Parquet written to {parquet_path}")

        # ------------------------------------------------------------------
        # Retention guard (FR‑012)
        # ------------------------------------------------------------------
        if retention_rate < self.config.get('retention_threshold', 0.95):
            self.logger.error(
                f"Retention rate {retention_rate:.2%} below threshold "
                f"{self.config['retention_threshold']:.2%}. Aborting."
            )
            # Exit with non‑zero status after files have been written
            raise SystemExit(1)

        return processed_df

    # ------------------------------------------------------------------
    # CLI entry point
    # ------------------------------------------------------------------
    def run_from_cli(self) -> None:
        """
        When the script is executed directly, load the first CSV found in
        ``data/raw/`` (produced by ``code/data/download.py``) and process it.
        If no raw CSV is present, fall back to the bundled sample dataset.
        """
        raw_dir = paths.data('raw')
        csv_files = list(raw_dir.glob('*.csv'))

        if not csv_files:
            # Fallback to the sample file shipped with the repo
            sample_path = Path('data') / 'sample_permeability.csv'
            if not sample_path.is_file():
                self.logger.error(
                    f"No CSV files found in raw data directory: {raw_dir} "
                    f"and no sample fallback available."
                )
                raise FileNotFoundError(f"No CSV files in {raw_dir}")
            self.logger.warning(
                f"No raw CSV found; using sample fallback at {sample_path}"
            )
            df = pd.read_csv(sample_path)
            # Align column names to expected defaults
            rename_map = {}
            if 'smiles' in df.columns and 'SMILES' not in df.columns:
                rename_map['smiles'] = 'SMILES'
            if 'permeability' in df.columns and 'permeability_coefficient' not in df.columns:
                rename_map['permeability'] = 'permeability_coefficient'
            if rename_map:
                df = df.rename(columns=rename_map)
        else:
            # Use the first CSV file (the download step writes a single file)
            csv_path = csv_files[0]
            self.logger.info(f"Loading raw dataset from {csv_path}")
            df = pd.read_csv(csv_path)

        # Process the dataframe; any SystemExit will propagate as the script exit code
        try:
            self.process(df)
        except SystemExit as e:
            raise e

if __name__ == "__main__":
    processor = MoleculeProcessor()
    try:
        processor.run_from_cli()
        # Successful run
        exit(0)
    except SystemExit as e:
        # Propagate the exit code
        exit(e.code if isinstance(e.code, int) else 1)
    except Exception as exc:
        log.error(f"Preprocessing failed: {exc}")
        exit(1)