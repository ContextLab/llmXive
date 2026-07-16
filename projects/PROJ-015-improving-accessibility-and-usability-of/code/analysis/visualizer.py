import matplotlib.pyplot as plt
import pandas as pd
from utils.logger import get_logger
import os
from pathlib import Path
import numpy as np

logger = get_logger(__name__)

class Visualizer:
    def __init__(self, processed_dir: Path, figures_dir: Path):
        self.processed_dir = processed_dir
        self.figures_dir = figures_dir
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        plt.style.use('default')

    def load_metrics(self) -> pd.DataFrame:
        metrics_path = self.processed_dir / "metrics_summary.csv"
        if not metrics_path.exists():
            raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
        return pd.read_csv(metrics_path)

    def load_cleaned_data(self) -> pd.DataFrame:
        cleaned_path = self.processed_dir / "cleaned_sessions.csv"
        if not cleaned_path.exists():
            raise FileNotFoundError(f"Cleaned data not found: {cleaned_path}")
        return pd.read_csv(cleaned_path)

    def plot_boxplot(self, df: pd.DataFrame, metric: str, x_col: str = "interface_type"):
        """Create a box plot with error bars for a specific metric."""
        plt.figure(figsize=(10, 6))
        data = df[df[metric].notna()]
        if data.empty:
            logger.warning(f"No data for {metric}")
            return

        # Group by interface type
        groups = data.groupby(x_col)[metric]
        means = groups.mean()
        stds = groups.std()
        
        # Plot
        bp = plt.boxplot([data[data[x_col] == val][metric] for val in data[x_col].unique()],
                         labels=data[x_col].unique(),
                         patch_artist=True)
        
        # Color the boxes
        colors = ['#a6cee3', '#1f78b4']
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
        
        # Add mean markers
        for i, val in enumerate(data[x_col].unique()):
            mean_val = data[data[x_col] == val][metric].mean()
            plt.plot(i+1, mean_val, 'r+', markersize=10, markeredgewidth=2)

        plt.title(f"{metric.replace('_', ' ').title()} by Interface Type")
        plt.xlabel("Interface Type")
        plt.ylabel(metric.replace('_', ' ').title())
        plt.grid(True, axis='y', alpha=0.3)
        
        filename = f"{metric}_boxplot.png"
        plt.savefig(self.figures_dir / filename, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Saved {filename}")

    def plot_error_bars(self, df: pd.DataFrame, metric: str, x_col: str = "interface_type"):
        """Create a plot with mean and error bars."""
        plt.figure(figsize=(8, 6))
        data = df[df[metric].notna()]
        if data.empty:
            return

        grouped = data.groupby(x_col)[metric]
        means = grouped.mean()
        sem = grouped.sem() # Standard Error of Mean
        
        x = np.arange(len(means))
        plt.bar(x, means, yerr=sem, capsize=5, color=['#a6cee3', '#1f78b4'], edgecolor='black')
        plt.xticks(x, means.index)
        plt.title(f"{metric.replace('_', ' ').title()} with Error Bars")
        plt.ylabel(metric.replace('_', ' ').title())
        plt.grid(axis='y', alpha=0.3)

        filename = f"{metric}_errorbars.png"
        plt.savefig(self.figures_dir / filename, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Saved {filename}")

    def run_all_plots(self):
        """Generate all standard plots."""
        try:
            df = self.load_cleaned_data()
            metrics_to_plot = ["completion_time", "error_count", "sus_score"]
            
            for metric in metrics_to_plot:
                if metric in df.columns:
                    self.plot_boxplot(df, metric)
                    self.plot_error_bars(df, metric)
                else:
                    logger.warning(f"Metric {metric} not found in cleaned data")
                    
        except Exception as e:
            logger.error(f"Error generating plots: {e}")
            raise

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--processed", type=str, required=True)
    parser.add_argument("--figures", type=str, required=True)
    args = parser.parse_args()
    
    viz = Visualizer(Path(args.processed), Path(args.figures))
    viz.run_all_plots()

if __name__ == "__main__":
    main()
