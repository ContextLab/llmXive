"""
Visualization utilities for RSA matrices and decoding accuracy.
"""
import matplotlib.pyplot as plt
import numpy as np
import logging
from pathlib import Path
import code.config as config

logger = logging.getLogger(__name__)

def plot_rsa_matrix(matrix, title="RSA Matrix", save_path=None):
    """
    Plot a Representational Similarity Analysis (RSA) matrix.
    
    Args:
        matrix: 2D numpy array representing the dissimilarity matrix.
        title: Plot title.
        save_path: Optional path to save the figure.
    """
    plt.figure(figsize=(8, 6))
    plt.imshow(matrix, cmap='viridis', interpolation='nearest')
    plt.title(title)
    plt.colorbar(label="Dissimilarity")
    
    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"Saved RSA matrix plot to {save_path}")
    else:
        plt.show()
    plt.close()

def plot_decoding_accuracy(accuracies, chance_level=0.0, title="Decoding Accuracy", save_path=None):
    """
    Plot decoding accuracies with chance level baseline.
    
    Args:
        accuracies: List or array of accuracy scores.
        chance_level: Baseline chance accuracy.
        title: Plot title.
        save_path: Optional path to save the figure.
    """
    plt.figure(figsize=(10, 6))
    x = np.arange(len(accuracies))
    plt.bar(x, accuracies, color='skyblue', edgecolor='black', label='Observed')
    plt.axhline(y=chance_level, color='red', linestyle='--', label=f'Chance ({chance_level:.2f})')
    
    plt.xlabel('Condition / ROI')
    plt.ylabel('Accuracy')
    plt.title(title)
    plt.xticks(x, [f'Cond {i+1}' for i in x])
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    
    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"Saved decoding accuracy plot to {save_path}")
    else:
        plt.show()
    plt.close()
