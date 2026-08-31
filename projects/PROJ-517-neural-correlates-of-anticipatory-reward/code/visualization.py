import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from logging_config import get_logger

logger = get_logger(__name__)

def plot_firing_rate_vs_reward(df: pd.DataFrame, output_path: Path) -> None:
    """Generate scatter plot of firing rate vs reward magnitude."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x='reward_magnitude', y='spike_count')
    plt.title("Firing Rate vs Reward Magnitude")
    plt.xlabel("Reward Magnitude")
    plt.ylabel("Spike Count (Firing Rate)")
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Plot generated: {output_path}")

def generate_visualization_report(df: pd.DataFrame, output_dir: Path) -> None:
    """Generate all visualization reports."""
    plot_path = output_dir / "firing_rate_vs_reward.png"
    plot_firing_rate_vs_reward(df, plot_path)

def main():
    pass

if __name__ == "__main__":
    main()
