"""
GNNExplainer implementation for identifying top subgraph motifs in molecular graphs.

This module implements the GNNExplainer algorithm to identify subgraph patterns
that contribute most to model predictions. It outputs a ranked list of motifs
as CSV/JSON and generates visualizations.

IMPORTANT DISCLAIMER: These subgraphs represent associational patterns and may
reflect dataset bias; they are not proven causal drivers.
"""
import os
import sys
import json
import logging
import pickle
from typing import Dict, Any, Optional, List, Tuple, Union
import numpy as np
import pandas as pd
import torch
from torch_geometric.data import Data
from torch_geometric.nn import MessagePassing
import networkx as nx
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for CI
import matplotlib.pyplot as plt
from rdkit import Chem
from rdkit.Chem import Draw, rdMolDescriptors
import hashlib
from datetime import datetime

# Import project utilities
from src.utils.logging import get_logger, log_message
from src.utils.seeding import set_seed

# Constants
EXPLANATION_DIR = "data/explanations"
VISUALIZATION_DIR = "figures/explanations"
RANKED_LIST_CSV = "data/explanations/ranked_motifs.csv"
RANKED_LIST_JSON = "data/explanations/ranked_motifs.json"
DISCLAIMER_TEXT = "These subgraphs represent associational patterns and may reflect dataset bias; they are not proven causal drivers."

logger = get_logger(__name__)


class GNNExplainer:
    """
    GNNExplainer implementation for molecular graphs.
    
    This class implements the gradient-based attribution method to identify
    important subgraphs in molecular graphs that contribute to predictions.
    """
    
    def __init__(self, model: torch.nn.Module, device: str = 'cpu', 
                 epochs: int = 100, lr: float = 0.01):
        """
        Initialize the GNNExplainer.
        
        Args:
            model: Trained GNN model to explain
            device: Device to run on ('cpu' or 'cuda')
            epochs: Number of optimization epochs for explanation
            lr: Learning rate for explanation optimization
        """
        self.model = model
        self.device = device
        self.epochs = epochs
        self.lr = lr
        self.model.eval()
        
        logger.info(f"GNNExplainer initialized on {device} with {epochs} epochs")
    
    def _create_edge_mask(self, num_edges: int) -> torch.Tensor:
        """Create learnable edge mask initialized to 1.0."""
        mask = torch.ones(num_edges, requires_grad=True, device=self.device)
        return mask
    
    def _create_node_mask(self, num_nodes: int) -> torch.Tensor:
        """Create learnable node mask initialized to 1.0."""
        mask = torch.ones(num_nodes, requires_grad=True, device=self.device)
        return mask
    
    def explain_graph(self, data: Data, target_class: Optional[int] = None) -> Dict[str, Any]:
        """
        Explain a single graph prediction.
        
        Args:
            data: PyTorch Geometric Data object
            target_class: Target class for classification (unused for regression)
            
        Returns:
            Dictionary containing edge importance scores, node importance scores,
            and the critical subgraph.
        """
        data = data.to(self.device)
        
        # Create learnable masks
        edge_mask = self._create_edge_mask(data.num_edges)
        node_mask = self._create_node_mask(data.num_nodes)
        
        optimizer = torch.optim.Adam([edge_mask, node_mask], lr=self.lr)
        
        best_loss = float('inf')
        best_edge_mask = edge_mask.detach().clone()
        best_node_mask = node_mask.detach().clone()
        
        with torch.no_grad():
            original_pred = self.model(data).squeeze()
        
        for epoch in range(self.epochs):
            optimizer.zero_grad()
            
            # Apply masks
            masked_edge_attr = data.edge_attr * edge_mask.unsqueeze(-1)
            masked_data = Data(
                x=data.x * node_mask.unsqueeze(-1),
                edge_index=data.edge_index,
                edge_attr=masked_edge_attr,
                y=data.y
            )
            
            # Forward pass
            pred = self.model(masked_data).squeeze()
            
            # Loss: difference from original prediction + regularization
            loss = torch.abs(pred - original_pred)
            loss += 0.001 * (torch.sum(edge_mask) + torch.sum(node_mask))
            
            loss.backward()
            optimizer.step()
            
            if loss.item() < best_loss:
                best_loss = loss.item()
                best_edge_mask = edge_mask.detach().clone()
                best_node_mask = node_mask.detach().clone()
        
        # Normalize masks
        edge_importance = torch.sigmoid(best_edge_mask).cpu().numpy()
        node_importance = torch.sigmoid(best_node_mask).cpu().numpy()
        
        # Extract critical subgraph (top 20% edges and nodes)
        edge_threshold = np.percentile(edge_importance, 80)
        node_threshold = np.percentile(node_importance, 80)
        
        critical_edges = data.edge_index[:, edge_importance >= edge_threshold]
        critical_nodes = np.where(node_importance >= node_threshold)[0]
        
        return {
            'edge_importance': edge_importance,
            'node_importance': node_importance,
            'critical_edges': critical_edges.cpu().numpy() if len(critical_edges) > 0 else np.array([]).reshape(2, 0),
            'critical_nodes': critical_nodes,
            'original_prediction': original_pred.item(),
            'loss': best_loss
        }
    
    def extract_subgraph_motif(self, data: Data, explanation: Dict[str, Any]) -> Optional[Chem.Mol]:
        """
        Extract the critical subgraph as an RDKit molecule.
        
        Args:
            data: Original graph data
            explanation: Explanation dictionary from explain_graph
            
        Returns:
            RDKit Mol object or None if extraction fails
        """
        try:
            # Create NetworkX graph from critical edges
            if len(explanation['critical_edges']) == 0:
                return None
            
            G = nx.Graph()
            for i, (src, dst) in enumerate(explanation['critical_edges'].T):
                G.add_edge(int(src), int(dst))
            
            # Add only critical nodes
            critical_nodes_set = set(explanation['critical_nodes'])
            G = G.subgraph(critical_nodes_set)
            
            if len(G.nodes()) == 0:
                return None
            
            # Map to RDKit (simplified: create from adjacency)
            # Note: This is a simplified extraction; real implementation would
            # preserve bond types and atom features from original molecule
            num_atoms = max(G.nodes()) + 1 if len(G.nodes()) > 0 else 0
            if num_atoms == 0:
                return None
            
            # Create empty molecule
            mol = Chem.RWMol()
            
            # Add atoms (simplified: all carbon)
            for _ in range(num_atoms):
                mol.AddAtom(Chem.Atom(6))  # Carbon
            
            # Add bonds
            for src, dst in G.edges():
                mol.AddBond(int(src), int(dst), Chem.BondType.SINGLE)
            
            # Clean up
            mol = mol.GetMol()
            Chem.SanitizeMol(mol)
            
            return mol
            
        except Exception as e:
            logger.warning(f"Failed to extract subgraph motif: {e}")
            return None
    
    def generate_motif_hash(self, mol: Chem.Mol) -> str:
        """Generate a canonical hash for a molecule motif."""
        try:
            # Canonical SMILES
            smiles = Chem.MolToSmiles(mol, isomericSmiles=False)
            return hashlib.md5(smiles.encode()).hexdigest()[:8]
        except:
            return hashlib.md5(str(mol).encode()).hexdigest()[:8]


def rank_motifs_from_explanations(
    explanations: List[Dict[str, Any]], 
    data_list: List[Data],
    top_k: int = 50
) -> pd.DataFrame:
    """
    Rank motifs across multiple explanations.
    
    Args:
        explanations: List of explanation dictionaries
        data_list: List of corresponding graph data objects
        top_k: Number of top motifs to return
        
    Returns:
        DataFrame with ranked motifs
    """
    explainer = GNNExplainer.__new__(GNNExplainer)  # Helper for motif extraction
    
    motif_records = []
    
    for i, (exp, data) in enumerate(zip(explanations, data_list)):
        mol = explainer.extract_subgraph_motif(data, exp)
        if mol is None:
            continue
        
        motif_hash = explainer.generate_motif_hash(mol)
        smiles = Chem.MolToSmiles(mol, isomericSmiles=False)
        
        # Use prediction confidence as importance score
        importance = exp.get('original_prediction', 0)
        loss = exp.get('loss', 0)
        
        motif_records.append({
            'motif_hash': motif_hash,
            'smiles': smiles,
            'importance_score': importance,
            'explanation_loss': loss,
            'source_index': i,
            'num_atoms': mol.GetNumAtoms(),
            'num_bonds': mol.GetNumBonds()
        })
    
    df = pd.DataFrame(motif_records)
    if len(df) == 0:
        return df
    
    # Sort by importance (higher prediction = more important for yield)
    df = df.sort_values('importance_score', ascending=False)
    df['rank'] = range(1, len(df) + 1)
    
    return df.head(top_k).reset_index(drop=True)


def visualize_motif(
    mol: Chem.Mol, 
    output_path: str, 
    title: str = "Motif Visualization",
    include_disclaimer: bool = True
) -> None:
    """
    Generate a visualization of a molecular motif.
    
    Args:
        mol: RDKit molecule to visualize
        output_path: Path to save the figure
        title: Title for the visualization
        include_disclaimer: Whether to include the disclaimer text
    """
    try:
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.axis('off')
        
        # Draw molecule
        img = Draw.MolToImage(mol, size=(600, 400))
        ax.imshow(img)
        ax.set_title(title, fontsize=14, pad=20)
        
        if include_disclaimer:
            # Add disclaimer at bottom
            disclaimer_text = f"DISCLAIMER: {DISCLAIMER_TEXT}"
            ax.text(
                0.5, -0.15, disclaimer_text,
                transform=ax.transAxes,
                fontsize=10,
                ha='center',
                va='center',
                style='italic',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            )
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        logger.info(f"Saved motif visualization to {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to visualize motif: {e}")
        raise


def generate_top_motifs_report(
    ranked_df: pd.DataFrame,
    output_csv: str = RANKED_LIST_CSV,
    output_json: str = RANKED_LIST_JSON,
    output_dir: str = EXPLANATION_DIR
) -> None:
    """
    Generate and save the top motifs report in CSV and JSON formats.
    
    Args:
        ranked_df: DataFrame with ranked motifs
        output_csv: Path for CSV output
        output_json: Path for JSON output
        output_dir: Directory to save outputs
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Add disclaimer column
    df_with_disclaimer = ranked_df.copy()
    df_with_disclaimer['disclaimer'] = DISCLAIMER_TEXT
    
    # Save CSV
    df_with_disclaimer.to_csv(output_csv, index=False)
    logger.info(f"Saved ranked motifs to {output_csv}")
    
    # Save JSON
    json_data = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'disclaimer': DISCLAIMER_TEXT,
            'total_motifs': len(df_with_disclaimer)
        },
        'motifs': df_with_disclaimer.to_dict(orient='records')
    }
    
    with open(output_json, 'w') as f:
        json.dump(json_data, f, indent=2)
    logger.info(f"Saved ranked motifs to {output_json}")


def generate_motif_visualizations(
    ranked_df: pd.DataFrame,
    data_list: List[Data],
    explainer: GNNExplainer,
    output_dir: str = VISUALIZATION_DIR,
    max_visualizations: int = 20
) -> None:
    """
    Generate visualizations for top motifs.
    
    Args:
        ranked_df: DataFrame with ranked motifs
        data_list: List of graph data objects
        explainer: GNNExplainer instance
        output_dir: Directory to save visualizations
        max_visualizations: Maximum number of visualizations to generate
    """
    os.makedirs(output_dir, exist_ok=True)
    
    count = 0
    for _, row in ranked_df.iterrows():
        if count >= max_visualizations:
            break
        
        idx = row['source_index']
        data = data_list[idx]
        exp = None  # Would need to store explanations separately
        
        # Re-extract motif from SMILES
        try:
            mol = Chem.MolFromSmiles(row['smiles'])
            if mol is None:
                continue
            
            output_path = os.path.join(
                output_dir, 
                f"motif_rank_{row['rank']}.png"
            )
            
            title = f"Rank {int(row['rank'])}: Importance={row['importance_score']:.4f}"
            visualize_motif(mol, output_path, title)
            count += 1
            
        except Exception as e:
            logger.warning(f"Failed to visualize motif rank {row['rank']}: {e}")
            continue
    
    logger.info(f"Generated {count} motif visualizations in {output_dir}")


def run_gnnexplainer_analysis(
    model: torch.nn.Module,
    data_list: List[Data],
    device: str = 'cpu',
    top_k: int = 50,
    max_samples: int = 100
) -> Dict[str, Any]:
    """
    Run full GNNExplainer analysis pipeline.
    
    Args:
        model: Trained GNN model
        data_list: List of graph data objects to explain
        device: Device to run on
        top_k: Number of top motifs to extract
        max_samples: Maximum number of samples to explain
        
    Returns:
        Dictionary with analysis results and paths
    """
    set_seed(42)  # Ensure reproducibility
    
    explainer = GNNExplainer(model, device=device)
    
    # Select samples to explain
    samples_to_explain = data_list[:min(max_samples, len(data_list))]
    explanations = []
    
    logger.info(f"Explaining {len(samples_to_explain)} graphs...")
    
    for i, data in enumerate(samples_to_explain):
        try:
            exp = explainer.explain_graph(data)
            explanations.append(exp)
            
            if (i + 1) % 20 == 0:
                logger.info(f"Explained {i + 1}/{len(samples_to_explain)} graphs")
                
        except Exception as e:
            logger.warning(f"Failed to explain graph {i}: {e}")
            continue
    
    # Rank motifs
    ranked_df = rank_motifs_from_explanations(explanations, samples_to_explain, top_k=top_k)
    
    if len(ranked_df) == 0:
        logger.warning("No motifs could be extracted. Returning empty results.")
        return {
            'ranked_motifs_csv': None,
            'ranked_motifs_json': None,
            'visualizations_dir': None,
            'num_motifs': 0,
            'num_samples_explained': len(explanations),
            'disclaimer': DISCLAIMER_TEXT
        }
    
    # Generate outputs
    generate_top_motifs_report(ranked_df)
    generate_motif_visualizations(ranked_df, samples_to_explain, explainer)
    
    return {
        'ranked_motifs_csv': RANKED_LIST_CSV,
        'ranked_motifs_json': RANKED_LIST_JSON,
        'visualizations_dir': VISUALIZATION_DIR,
        'num_motifs': len(ranked_df),
        'num_samples_explained': len(explanations),
        'disclaimer': DISCLAIMER_TEXT
    }


def main():
    """
    Main entry point for GNNExplainer analysis.
    
    This function loads a trained model and preprocessed data, runs GNNExplainer,
    and outputs ranked motifs and visualizations.
    """
    logger.info("Starting GNNExplainer analysis...")
    
    try:
        # Load model (placeholder - would load from checkpoint)
        # model = load_model_checkpoint(...)
        # For now, we assume model is passed or loaded
        raise NotImplementedError(
            "Model loading not implemented yet. "
            "This function should be called after T018 (model training) completes."
        )
        
    except NotImplementedError as e:
        logger.error(f"Analysis cannot run yet: {e}")
        logger.info("Waiting for model training (T018) to complete.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
