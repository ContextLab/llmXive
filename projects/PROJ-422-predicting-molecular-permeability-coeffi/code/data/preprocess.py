import logging
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors, Lipinski
from rdkit import RDLogger
import pandas as pd
import numpy as np
import yaml
import os

# Suppress RDKit warnings for cleaner logs
RDLogger.DisableLog('rdApp.*')

class MoleculeProcessor:
    """
    Handles SMILES parsing, descriptor calculation, graph feature extraction,
    and bias checking as per project specifications.
    """

    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)
        self.descriptor_names = [
            'MW', 'LogP', 'TPSA', 'NumRotatableBonds', 'NumHAcceptors',
            'NumHDonors', 'NumAromaticRings', 'NumAliphaticRings',
            'NumHeteroatoms', 'FractionCSP3', 'HeavyAtomCount'
        ]

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if config_path is None:
            # Default path relative to project root
            config_path = "projects/PROJ-422-predicting-molecular-permeability-coeffi/config.yaml"
        
        if not os.path.exists(config_path):
            self.logger.warning(f"Config file not found at {config_path}, using defaults.")
            return {'bias_threshold': 0.85, 'retention_threshold': 0.95}

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Ensure defaults exist
        return {
            'bias_threshold': config.get('bias_threshold', 0.85),
            'retention_threshold': config.get('retention_threshold', 0.95)
        }

    def parse_smiles(self, smiles: str) -> Optional[Chem.Mol]:
        """
        Parse SMILES string into an RDKit molecule object.
        Returns None if the SMILES is invalid.
        """
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        # Sanitize to catch common issues
        try:
            Chem.SanitizeMol(mol)
        except Exception:
            return None
        return mol

    def calculate_descriptors(self, mol: Chem.Mol) -> Dict[str, float]:
        """
        Calculate standard molecular descriptors for a given molecule.
        """
        descriptors = {}
        try:
            descriptors['MW'] = Descriptors.MolWt(mol)
            descriptors['LogP'] = Descriptors.MolLogP(mol)
            descriptors['TPSA'] = Descriptors.TPSA(mol)
            descriptors['NumRotatableBonds'] = Lipinski.NumRotatableBonds(mol)
            descriptors['NumHAcceptors'] = Lipinski.NumHAcceptors(mol)
            descriptors['NumHDonors'] = Lipinski.NumHDonors(mol)
            descriptors['NumAromaticRings'] = rdMolDescriptors.CalcNumAromaticRings(mol)
            descriptors['NumAliphaticRings'] = rdMolDescriptors.CalcNumAliphaticRings(mol)
            descriptors['NumHeteroatoms'] = rdMolDescriptors.CalcNumHeteroatoms(mol)
            descriptors['FractionCSP3'] = rdMolDescriptors.CalcFractionCSP3(mol)
            descriptors['HeavyAtomCount'] = rdMolDescriptors.CalcNumHeavyAtoms(mol)
        except Exception as e:
            self.logger.warning(f"Error calculating descriptors: {e}")
            return {}
        
        return descriptors

    def calculate_graph_features(self, mol: Chem.Mol) -> Dict[str, float]:
        """
        Calculate flattened graph statistics for ablation studies.
        These represent topological properties derived from the molecular graph.
        """
        if mol is None:
            return {}

        graph_features = {}
        try:
            # Get adjacency matrix
            adj = Chem.rdmolops.GetAdjacencyMatrix(mol)
            degree_list = np.sum(adj, axis=1)
            
            graph_features['mean_degree'] = float(np.mean(degree_list))
            graph_features['max_degree'] = float(np.max(degree_list))
            graph_features['min_degree'] = float(np.min(degree_list))
            graph_features['degree_std'] = float(np.std(degree_list))
            
            # Connectivity metrics
            graph_features['num_edges'] = float(np.sum(adj) / 2)
            graph_features['num_nodes'] = float(mol.GetNumAtoms())
            
            # Substructure counts (approximated via ring systems)
            ring_info = mol.GetRingInfo()
            graph_features['num_rings'] = float(len(ring_info.Rings()))
            graph_features['num_fused_rings'] = float(len([r for r in ring_info.Rings() if len(r) > 1]))
            
            # Path lengths (shortest path average)
            # Note: This is computationally expensive for large molecules, using a subset if needed
            if mol.GetNumAtoms() < 100:
                sp_lengths = []
                for i in range(mol.GetNumAtoms()):
                    for j in range(i + 1, mol.GetNumAtoms()):
                        path = Chem.GetShortestPath(mol, i, j)
                        if path:
                            sp_lengths.append(len(path))
                if sp_lengths:
                    graph_features['avg_shortest_path'] = float(np.mean(sp_lengths))
                else:
                    graph_features['avg_shortest_path'] = 0.0
            else:
                graph_features['avg_shortest_path'] = 0.0 # Skip for very large molecules
                
        except Exception as e:
            self.logger.warning(f"Error calculating graph features: {e}")
        
        return graph_features

    def process_dataframe(self, df: pd.DataFrame, smiles_col: str = 'SMILES', 
                          target_col: str = 'permeability_coefficient') -> Tuple[pd.DataFrame, int, int]:
        """
        Process a dataframe of molecules: parse SMILES, calculate descriptors,
        handle invalid data, and perform bias checks.
        
        Returns:
          - Processed dataframe
          - Number of valid molecules
          - Number of invalid molecules
        """
        self.logger.info(f"Processing {len(df)} molecules...")
        
        valid_rows = []
        invalid_count = 0
        
        for idx, row in df.iterrows():
            smiles = row[smiles_col]
            mol = self.parse_smiles(smiles)
            
            if mol is None:
                invalid_count += 1
                continue
            
            # Calculate descriptors
            descriptors = self.calculate_descriptors(mol)
            if not descriptors:
                invalid_count += 1
                continue
            
            # Calculate graph features
            graph_features = self.calculate_graph_features(mol)
            
            # Combine all features
            new_row = row.to_dict()
            new_row.update(descriptors)
            new_row.update(graph_features)
            new_row['valid_mol'] = True
            
            valid_rows.append(new_row)
        
        valid_count = len(valid_rows)
        retention_rate = valid_count / len(df) if len(df) > 0 else 0.0
        
        self.logger.info(f"Valid molecules: {valid_count}, Invalid: {invalid_count}")
        self.logger.info(f"Retention rate: {retention_rate:.2%}")
        
        # Check retention threshold (FR-011)
        threshold = self.config.get('retention_threshold', 0.95)
        if retention_rate < threshold:
            self.logger.error(f"Retention rate {retention_rate:.2%} is below threshold {threshold:.2%}. Exiting.")
            raise SystemExit(1)
        
        processed_df = pd.DataFrame(valid_rows)
        
        # Perform bias check (FR-013)
        self._check_bias(processed_df, target_col)
        
        return processed_df, valid_count, invalid_count

    def _check_bias(self, df: pd.DataFrame, target_col: str) -> None:
        """
        Implement FR-013: Bias Check.
        Calculate correlation between input descriptors and target variable.
        If correlation exceeds threshold, flag results and log warning.
        """
        self.logger.info("Performing bias check (FR-013)...")
        
        # Define descriptor columns to check (exclude graph features for this specific check 
        # as per typical bias check focus on standard physicochemical properties)
        # We check the standard descriptors calculated in calculate_descriptors
        descriptor_cols = [col for col in self.descriptor_names if col in df.columns]
        
        if not descriptor_cols:
            self.logger.warning("No standard descriptor columns found for bias check.")
            return
        
        if target_col not in df.columns:
            self.logger.warning(f"Target column '{target_col}' not found in dataframe. Skipping bias check.")
            return
        
        bias_threshold = self.config.get('bias_threshold', 0.85)
        high_correlations = []
        
        for col in descriptor_cols:
            # Calculate Pearson correlation
            corr_matrix = df[[col, target_col]].corr()
            corr_val = corr_matrix.loc[col, target_col]
            
            if abs(corr_val) > bias_threshold:
                high_correlations.append((col, corr_val))
                self.logger.warning(f"HIGH CORRELATION DETECTED: {col} vs {target_col} = {corr_val:.4f}")
        
        if high_correlations:
            warning_msg = "potentially confounded"
            self.logger.warning(f"Bias Warning: {warning_msg}. High correlations found: {high_correlations}")
            # Store the warning in the dataframe for downstream consumption
            df['bias_warning'] = warning_msg
            # Log specific high correlations to a separate file if needed
            self.logger.info(f"Saving bias check details to logs...")
        else:
            self.logger.info("Bias check passed. No descriptors exceed correlation threshold.")
            df['bias_warning'] = None

def main():
    """
    Main entry point for the preprocessing script.
    This function is intended to be called by a pipeline runner.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Example usage (would be replaced by actual pipeline integration)
    # In a real scenario, this would read from data/raw, process, and save to data/processed
    logger.info("Preprocessing module initialized.")
    logger.info("To run: Instantiate MoleculeProcessor and call process_dataframe().")

if __name__ == "__main__":
    main()