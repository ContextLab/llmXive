"""
Visualization module for polymer degradation pathways.
Generates molecular graphs with highlighted attribution scores and
permutation test result plots.
"""
import os
import json
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import networkx as nx
import rdkit
from rdkit import Chem
from rdkit.Chem import Draw, Descriptors
from rdkit.Chem.Draw import rdMolDraw2D

from utils import get_project_paths, get_logger
from data_models import PolymerRecord, MolecularGraph
from evaluate import load_trained_model_and_ig, load_test_predictions

# Configure logging
logger = get_logger(__name__)

def get_highlight_colors(atom_indices: List[int], scores: List[float], max_score: float) -> List[Tuple[float, float, float, float]]:
    """
    Generate RGBA colors for atoms based on their importance scores.
    Higher scores = more red, lower scores = transparent.
    """
    colors = []
    for score in scores:
        # Normalize score to 0-1 range
        norm_score = min(score / max_score, 1.0) if max_score > 0 else 0.0
        # Map to red intensity (0.2 to 1.0)
        r = 0.2 + 0.8 * norm_score
        g = 0.2 * (1.0 - norm_score)
        b = 0.2 * (1.0 - norm_score)
        a = 0.3 + 0.7 * norm_score
        colors.append((r, g, b, a))
    return colors

def visualize_molecule_with_attribution(
    smiles: str,
    atom_importance: Dict[int, float],
    output_path: Path,
    title: Optional[str] = None
) -> bool:
    """
    Generate a visualization of a molecule with atoms colored by importance scores.
    
    Args:
        smiles: SMILES string of the molecule
        atom_importance: Dictionary mapping atom indices to importance scores
        output_path: Path to save the visualization
        title: Optional title for the plot
    
    Returns:
        True if successful, False otherwise
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.error(f"Failed to parse SMILES: {smiles}")
            return False

        # Prepare atom colors
        atom_scores = [atom_importance.get(i, 0.0) for i in range(mol.GetNumAtoms())]
        max_score = max(atom_scores) if atom_scores else 1.0
        colors = get_highlight_colors(list(range(len(atom_scores))), atom_scores, max_score)

        # Create drawer
        drawer = rdMolDraw2D.MolDraw2DCairo(600, 400)
        drawer.SetFontSize(0.8)
        
        # Draw molecule with custom atom colors
        op = rdMolDraw2D.MolDrawOptions()
        op.atomColourPalette = {i: rdMolDraw2D.rdBase.DrawingColor(*c) 
                               for i, c in enumerate(colors)}
        op.continuousHighlight = True
        op.highlightColour = (1.0, 0.0, 0.0)  # Red
        op.highlightWidth = 0.15
        op.atomLabelFontSize = 25
        op.dotsWidth = 1.5
        
        drawer.SetDrawOptions(op)
        rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol, 
                                          highlightAtoms=list(atom_importance.keys()))
        drawer.FinishDrawing()

        # Save to file
        with open(output_path, 'wb') as f:
            f.write(drawer.GetDrawingText())

        logger.info(f"Saved molecule visualization to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Error visualizing molecule: {e}", exc_info=True)
        return False

def plot_permutation_test_results(
    null_distribution: Dict[str, Any],
    observed_stat: float,
    output_path: Path,
    title: str = "Permutation Test Results"
) -> bool:
    """
    Generate a plot showing the null distribution and observed statistic.
    
    Args:
        null_distribution: Dictionary containing 'bins', 'counts', 'observed_stat', 'p_value'
        observed_stat: The observed test statistic
        output_path: Path to save the plot
        title: Title for the plot
    
    Returns:
        True if successful, False otherwise
    """
    try:
        bins = np.array(null_distribution.get('bins', []))
        counts = np.array(null_distribution.get('counts', []))
        p_value = null_distribution.get('p_value', 0.0)
        
        if len(bins) == 0 or len(counts) == 0:
            logger.error("Empty null distribution data")
            return False

        plt.figure(figsize=(10, 6))
        
        # Plot histogram of null distribution
        plt.bar(bins[:-1], counts, width=np.diff(bins), alpha=0.7, 
               color='skyblue', edgecolor='black', label='Null Distribution')
        
        # Plot observed statistic
        plt.axvline(x=observed_stat, color='red', linestyle='--', 
                   linewidth=2, label=f'Observed Statistic ({observed_stat:.4f})')
        
        # Add p-value annotation
        plt.annotate(f'p-value = {p_value:.4f}', 
                    xy=(observed_stat, max(counts) * 0.9),
                    xytext=(observed_stat + np.diff(bins)[0], max(counts) * 0.8),
                    arrowprops=dict(arrowstyle='->', color='red'),
                    fontsize=12, color='red')
        
        plt.xlabel('Test Statistic')
        plt.ylabel('Frequency')
        plt.title(title)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Save plot
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Saved permutation test plot to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Error plotting permutation results: {e}", exc_info=True)
        return False

def plot_attribution_distribution(
    attribution_scores: List[float],
    output_path: Path,
    title: str = "Feature Attribution Score Distribution"
) -> bool:
    """
    Generate a histogram of attribution scores.
    
    Args:
        attribution_scores: List of importance scores
        output_path: Path to save the plot
        title: Title for the plot
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if not attribution_scores:
            logger.error("Empty attribution scores list")
            return False

        plt.figure(figsize=(8, 6))
        plt.hist(attribution_scores, bins=30, alpha=0.7, color='steelblue', 
                edgecolor='black')
        plt.axvline(x=0, color='red', linestyle='--', linewidth=1, label='Zero')
        
        plt.xlabel('Attribution Score')
        plt.ylabel('Frequency')
        plt.title(title)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Saved attribution distribution plot to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Error plotting attribution distribution: {e}", exc_info=True)
        return False

def plot_ester_attribution_check(
    percentage: float,
    threshold: float,
    p_value: float,
    output_path: Path
) -> bool:
    """
    Generate a bar chart comparing ester attribution percentage to threshold.
    
    Args:
        percentage: Observed percentage of ester bonds in top attributions
        threshold: Threshold value for comparison
        p_value: P-value from null distribution comparison
        output_path: Path to save the plot
    
    Returns:
        True if successful, False otherwise
    """
    try:
        plt.figure(figsize=(8, 6))
        
        # Create bar chart
        x = ['Observed', 'Threshold']
        y = [percentage, threshold]
        colors = ['green' if percentage >= threshold else 'red', 'gray']
        
        bars = plt.bar(x, y, color=colors, edgecolor='black')
        
        # Add value labels on bars
        for bar, val in zip(bars, y):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                    f'{val:.2%}', ha='center', va='bottom', fontsize=12)
        
        # Add p-value annotation
        plt.annotate(f'p-value = {p_value:.4f}', 
                    xy=(0.5, max(y) * 1.1),
                    xytext=(0.5, max(y) * 1.2),
                    ha='center', fontsize=12, color='darkblue')
        
        plt.ylabel('Percentage')
        plt.title('Ester Bond Attribution Validation')
        plt.ylim(0, max(1.0, max(y) * 1.3))
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Saved ester attribution check plot to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Error plotting ester attribution check: {e}", exc_info=True)
        return False

def load_integration_gradients_maps(filepath: Path) -> List[Dict[str, Any]]:
    """
    Load Integrated Gradients attribution maps from JSON file.
    
    Args:
        filepath: Path to the IG maps JSON file
    
    Returns:
        List of attribution maps
    """
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load IG maps: {e}")
        return []

def load_permutation_results(filepath: Path) -> Dict[str, Any]:
    """
    Load permutation test results from JSON file.
    
    Args:
        filepath: Path to the results JSON file
    
    Returns:
        Permutation test results dictionary
    """
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load permutation results: {e}")
        return {}

def load_ester_attribution_check(filepath: Path) -> Dict[str, Any]:
    """
    Load ester attribution check results from JSON file.
    
    Args:
        filepath: Path to the results JSON file
    
    Returns:
        Ester attribution check dictionary
    """
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load ester attribution check: {e}")
        return {}

def generate_all_visualizations() -> bool:
    """
    Main function to generate all required visualizations.
    
    Returns:
        True if all visualizations were generated successfully, False otherwise
    """
    paths = get_project_paths()
    reports_dir = paths['reports']
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    total_count = 0
    
    # 1. Visualize sample molecules with attribution scores
    logger.info("Generating molecule attribution visualizations...")
    ig_maps_path = reports_dir / 'ig_attribution_maps.json'
    if ig_maps_path.exists():
        ig_maps = load_integration_gradients_maps(ig_maps_path)
        # Visualize first 5 molecules as examples
        for i, record in enumerate(ig_maps[:5]):
            total_count += 1
            smiles = record.get('smiles', '')
            atom_importance = {item['atom_index']: item['normalized_score'] 
                             for item in record.get('atom_importance', [])}
            if smiles and atom_importance:
                output_path = reports_dir / f'molecule_attribution_{i+1}.png'
                if visualize_molecule_with_attribution(smiles, atom_importance, output_path):
                    success_count += 1
    else:
        logger.warning("IG attribution maps not found, skipping molecule visualizations")
    
    # 2. Plot permutation test results
    logger.info("Generating permutation test visualization...")
    total_count += 1
    perm_results_path = reports_dir / 'permutation_test_results.json'
    if perm_results_path.exists():
        perm_results = load_permutation_results(perm_results_path)
        if perm_results:
            output_path = reports_dir / 'permutation_test_plot.png'
            if plot_permutation_test_results(
                perm_results, 
                perm_results.get('observed_stat', 0),
                output_path
            ):
                success_count += 1
    else:
        logger.warning("Permutation test results not found, skipping visualization")
    
    # 3. Plot attribution score distribution
    logger.info("Generating attribution score distribution...")
    total_count += 1
    if ig_maps_path.exists():
        ig_maps = load_integration_gradients_maps(ig_maps_path)
        all_scores = []
        for record in ig_maps:
            for item in record.get('atom_importance', []):
                all_scores.append(item.get('normalized_score', 0.0))
        
        if all_scores:
            output_path = reports_dir / 'attribution_distribution.png'
            if plot_attribution_distribution(all_scores, output_path):
                success_count += 1
    else:
        logger.warning("IG attribution maps not found, skipping distribution plot")
    
    # 4. Plot ester attribution check
    logger.info("Generating ester attribution check visualization...")
    total_count += 1
    ester_check_path = reports_dir / 'ester_attribution_check.json'
    if ester_check_path.exists():
        ester_check = load_ester_attribution_check(ester_check_path)
        if ester_check:
            output_path = reports_dir / 'ester_attribution_validation.png'
            if plot_ester_attribution_check(
                ester_check.get('percentage', 0),
                ester_check.get('threshold', 0),
                ester_check.get('p_value_null_comparison', 0),
                output_path
            ):
                success_count += 1
    else:
        logger.warning("Ester attribution check not found, skipping visualization")
    
    # Summary
    logger.info(f"Visualization generation complete: {success_count}/{total_count} successful")
    return success_count == total_count

def main():
    """Entry point for the visualization script."""
    logger.info("Starting visualization generation...")
    success = generate_all_visualizations()
    if success:
        logger.info("All visualizations generated successfully")
        return 0
    else:
        logger.error("Some visualizations failed to generate")
        return 1

if __name__ == '__main__':
    exit(main())
