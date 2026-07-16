import matplotlib.pyplot as plt
import pandas as pd
from utils.logger import get_logger
import os
from pathlib import Path
import numpy as np

logger = get_logger(__name__)

class Visualizer:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        plt.style.use('seaborn-v0_8-whitegrid')
    
    def create_boxplot(self, data: pd.DataFrame, metric: str, x_col: str = 'interface_type', 
                     y_col: str = None, title: str = None, output_file: str = None):
        """Create a box plot with error bars for a given metric."""
        if y_col is None:
            y_col = metric
        
        if metric not in data.columns or x_col not in data.columns:
            raise ValueError(f"Required columns not found. Available: {data.columns.tolist()}")
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Group data by interface type
        groups = data.groupby(x_col)[y_col]
        
        # Extract data for each group
        box_data = [group.dropna().values for name, group in groups]
        labels = [name for name, _ in groups]
        
        # Create box plot
        bp = ax.boxplot(box_data, labels=labels, patch_artist=True, showmeans=True)
        
        # Color the boxes
        colors = ['#3498db', '#e74c3c']
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        # Add mean points
        for i, group in enumerate(groups):
            mean_val = group.mean()
            ax.plot(i + 1, mean_val, 'g^', markersize=10, label='Mean' if i == 0 else "")
        
        # Labels and title
        if title is None:
            title = f"{metric.replace('_', ' ').title()} by Interface Type"
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel('Interface Type', fontsize=12)
        ax.set_ylabel(metric.replace('_', ' ').title(), fontsize=12)
        
        # Add legend if means are plotted
        if any(bp['fliers']):
            ax.legend(loc='upper right')
        
        plt.tight_layout()
        
        # Save plot
        if output_file is None:
            output_file = f"boxplot_{metric}.png"
        
        output_path = self.output_dir / output_file
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Box plot saved: {output_path}")
        return output_path
    
    def create_comparison_plot(self, data: pd.DataFrame, metrics: list, output_prefix: str = None):
        """Create box plots for multiple metrics."""
        if output_prefix is None:
            output_prefix = "boxplot"
        
        output_files = []
        for metric in metrics:
            if metric in data.columns:
                output_file = f"{output_prefix}_{metric}.png"
                try:
                    path = self.create_boxplot(data, metric, output_file=output_file)
                    output_files.append(path)
                except Exception as e:
                    logger.error(f"Failed to create plot for {metric}: {e}")
            else:
                logger.warning(f"Metric {metric} not found in data, skipping plot.")
        
        return output_files

def main():
    """Main entry point for visualization generation."""
    project_root = Path(__file__).resolve().parent.parent
    input_path = project_root / 'data' / 'processed' / 'cleaned_sessions.csv'
    output_dir = project_root / 'data' / 'processed'
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1
    
    try:
        # Load data
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows for visualization")
        
        # Create visualizer
        visualizer = Visualizer(output_dir)
        
        # Generate plots for key metrics
        metrics = ['completion_time', 'error_count', 'sus_score']
        output_files = visualizer.create_comparison_plot(df, metrics)
        
        if output_files:
            print(f"Generated {len(output_files)} plots:")
            for f in output_files:
                print(f"  - {f}")
            return 0
        else:
            print("No plots were generated.")
            return 1
            
    except Exception as e:
        logger.error(f"Visualization failed: {e}")
        print(f"Error: {e}")
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())