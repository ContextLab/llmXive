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
    Handles SMILES parsing, descriptor calculation, graph feature extraction,
    and final dataset generation that conforms to the dataset contract.
    """

    def __init__(self, config_path: Optional[str] = None, retention_threshold: Optional[float] = None):
        self.logger = logging.getLogger(__name__)
        # Load config for defaults
        self.config = self._load_config(config_path)
        
        # Allow overriding retention threshold (critical for unit tests)
        self.retention_threshold = retention_threshold if retention_threshold is not None else self.config.get('retention_threshold', 0.95)
        
        self.descriptor_names = [
            'mw', 'logp', 'tpsa', 'hba', 'hbd', 'rotatable_bonds'
        ]

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from a YAML file, falling back to defaults."""
        default_config = {
            'bias_threshold': 0.85,
            'retention_threshold': 0.95
        }
        if config_path is None:
            # Try project root config
            config_path = paths.root / "config.yaml"

        if not os.path.exists(config_path):
            return default_config

        try:
            with open(config_path, "r") as f:
                cfg = yaml.safe_load(f) or {}
            return {**default_config, **cfg}
        except Exception:
            return default_config

    def parse_smiles(self, smiles: str) -> Optional[Chem.Mol]:
        """Convert SMILES string into an RDKit Mol object."""
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

    def calculate_descriptors(self, mol: Chem.Mol) -> Dict[str, float]:
        """Compute required molecular descriptors."""
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
            return {}

    def calculate_graph_json(self, mol: Chem.Mol) -> Tuple[str, str]:
        """Produce JSON strings representing node and edge features."""
        node_list = []
        for idx, atom in enumerate(mol.GetAtoms()):
            node_list.append({
                'atom_idx': idx,
                'symbol': atom.GetSymbol(),
                'atomic_num': atom.GetAtomicNum(),
                'degree': atom.GetDegree(),
                'formal_charge': atom.GetFormalCharge(),
                'hybridization': str(atom.GetHybridization()),
                'aromatic': atom.GetIsAromatic()
            })

        edge_list = []
        for bond in mol.GetBonds():
            edge_list.append({
                'start': bond.GetBeginAtomIdx(),
                'end': bond.GetEndAtomIdx(),
                'bond_type': str(bond.GetBondType()),
                'aromatic': bond.GetIsAromatic()
            })

        return json.dumps(node_list), json.dumps(edge_list)

    def process(
        self, 
        df: pd.DataFrame, 
        smiles_col: str = 'SMILES', 
        target_col: str = 'permeability'
    ) -> pd.DataFrame:
        """
        End-to-end preprocessing.
        1. Parse SMILES (FR-011).
        2. Compute descriptors (FR-003).
        3. Build graph JSON (FR-002).
        4. Exclude missing targets.
        5. Write files BEFORE guard.
        6. Apply retention guard (FR-012).
        """
        self.logger.info(f"Processing {len(df)} records...")
        
        # Robust column detection
        actual_smiles_col = smiles_col if smiles_col in df.columns else ('smiles' if 'smiles' in df.columns else None)
        actual_target_col = target_col if target_col in df.columns else ('permeability_coefficient' if 'permeability_coefficient' in df.columns else ('target' if 'target' in df.columns else None))

        if actual_smiles_col is None:
            raise ValueError(f"SMILES column not found. Available: {df.columns.tolist()}")
        
        processed_rows = []
        valid_smiles_count = 0
        total_input_rows = len(df)

        for _, row in df.iterrows():
            smiles = row[actual_smiles_col]
            mol = self.parse_smiles(smiles)
            
            if mol is None:
                continue
            
            valid_smiles_count += 1
            
            # Target check: Exclude rows with missing permeability
            target_val = None
            if actual_target_col:
                target_val = row[actual_target_col]
            
            if pd.isna(target_val):
                continue

            descriptors = self.calculate_descriptors(mol)
            node_json, edge_json = self.calculate_graph_json(mol)

            new_row = {
                'smiles': smiles,
                'mol_valid': True,
                'mw': descriptors.get('mw', np.nan),
                'logp': descriptors.get('logp', np.nan),
                'tpsa': descriptors.get('tpsa', np.nan),
                'hba': descriptors.get('hba', np.nan),
                'hbd': descriptors.get('hbd', np.nan),
                'rotatable_bonds': descriptors.get('rotatable_bonds', np.nan),
                'target': target_val,
                'node_features': node_json,
                'edge_features': edge_json
            }
            if 'polymer_type' in df.columns:
                new_row['polymer_type'] = row['polymer_type']
            
            processed_rows.append(new_row)

        processed_df = pd.DataFrame(processed_rows)
        
        # Median imputation for descriptors
        for col in self.descriptor_names:
            if col in processed_df.columns:
                processed_df[col] = processed_df[col].fillna(processed_df[col].median())

        # Write outputs BEFORE guard checks
        csv_path = paths.data('processed', 'processed_data.csv')
        parquet_path = paths.data('processed', 'processed_data.parquet')
        
        processed_df.to_csv(csv_path, index=False)
        processed_df.to_parquet(parquet_path, index=False)
        self.logger.info(f"Written outputs to {csv_path} and {parquet_path}")

        # Retention guard
        retention_rate = valid_smiles_count / total_input_rows if total_input_rows > 0 else 0.0
        self.logger.info(f"Retention rate: {retention_rate:.2%}")
        
        if retention_rate < self.retention_threshold:
            self.logger.warning(f"Retention rate {retention_rate:.2%} below threshold {self.retention_threshold:.2%}")
            raise SystemExit(1)

        return processed_df

def run_from_cli(self) -> None:
    """CLI entry point to process raw data."""
    raw_dir = paths.data('raw')
    csv_files = list(raw_dir.glob('*.csv'))
    
    if not csv_files:
        # Fallback to sample
        sample_path = paths.root / "data" / "sample_permeability.csv"
        if not sample_path.exists():
            self.logger.error("No raw data found.")
            sys.exit(1)
        df = pd.read_csv(sample_path)
    else:
        df = pd.read_csv(csv_files[0])

    try:
        self.process(df)
    except SystemExit as e:
        sys.exit(e.code if isinstance(e.code, int) else 1)

if __name__ == "__main__":
    processor = MoleculeProcessor()
    processor.run_from_cli()
