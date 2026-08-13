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
    Plot a Representational Similarity Analysis (RSA) dissimilarity matrix.
    """
    plt.figure(figsize=(8, 6))
    plt.imshow(matrix, cmap='coolwarm', interpolation='nearest')
    plt.colorbar(label='Dissimilarity')
    plt.title(title)
    plt.xlabel("Events")
    plt.ylabel("Events")

    if save_path:
        plt.savefig(save_path, dpi=300)
        logger.info(f"RSA matrix saved to {save_path}")
    else:
        # Default save path if not provided
        default_path = Path(config.FIGURES_DIR) / f"rsa_{title.replace(' ', '_')}.png"
        plt.savefig(default_path, dpi=300)
        logger.info(f"RSA matrix saved to {default_path}")
    plt.close()

def plot_decoding_accuracy(accuracies, chance_level, title="Decoding Accuracy", save_path=None):
    """
    Plot decoding accuracy with chance baseline.
    """
    plt.figure(figsize=(8, 6))
    plt.bar(range(len(accuracies)), accuracies, color='skyblue', label='Accuracy')
    plt.axhline(y=chance_level, color='r', linestyle='--', label=f'Chance ({chance_level:.2f})')
    plt.xlabel("Fold / Category")
    plt.ylabel("Accuracy")
    plt.title(title)
    plt.legend()

    if save_path:
        plt.savefig(save_path, dpi=300)
        logger.info(f"Decoding accuracy plot saved to {save_path}")
    else:
        default_path = Path(config.FIGURES_DIR) / f"decoding_{title.replace(' ', '_')}.png"
        plt.savefig(default_path, dpi=300)
        logger.info(f"Decoding accuracy plot saved to {default_path}")
    plt.close()
