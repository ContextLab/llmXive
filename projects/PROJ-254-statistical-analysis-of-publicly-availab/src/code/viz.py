import os
import logging
from pathlib import Path
from typing import List, Dict, Any
import numpy as np

from utils import get_logger, setup_logging, set_deterministic_seed
from memory_utils import monitor_and_maybe_gc

def generate_similarity_trend_plot(
    similarity_data: List[Dict[str, Any]],
    output_path: str = "figures/similarity_trend.png"
) -> None:
    """
    Generate line plot of similarity trend over time.

    Args:
        similarity_data: List of similarity results.
        output_path: Path to save the plot.
    """
    logger = get_logger()
    logger.info("Generating similarity trend plot...")

    try:
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
        import matplotlib.pyplot as plt

        years = [d['year'] for d in similarity_data]
        similarities = [d['mean_off_diagonal_similarity'] for d in similarity_data]

        plt.figure(figsize=(10, 6))
        plt.plot(years, similarities, marker='o', linestyle='-', color='b')
        plt.xlabel('Year')
        plt.ylabel('Mean Off-Diagonal Similarity')
        plt.title('Genre Similarity Trend Over Time')
        plt.grid(True, alpha=0.3)

        # Add 95% CI bands (placeholder - would need actual CI calculation)
        # For now, just show the trend line

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        logger.info(f"Saved trend plot to {output_path}")

    except ImportError as e:
        logger.error(f"matplotlib not available: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error generating trend plot: {str(e)}")
        raise

def generate_genre_similarity_heatmap(
  similarity_data: List[Dict[str, Any]],
  output_path: str = "figures/genre_similarity_heatmap.html"
) -> None:
    """
    Generate interactive heatmap of genre similarities.

    Args:
        similarity_data: List of similarity results.
        output_path: Path to save the heatmap.
    """
    logger = get_logger()
    logger.info("Generating genre similarity heatmap...")

    try:
        import plotly.graph_objects as go
        import pandas as pd

        df = pd.DataFrame(similarity_data)

        fig = go.Figure(data=go.Heatmap(
            z=[df['mean_off_diagonal_similarity']],
            x=df['year'],
            y=['Similarity'],
            colorscale='Viridis',
            colorbar=dict(title='Similarity')
        ))

        fig.update_layout(
            title='Genre Similarity Heatmap',
            xaxis_title='Year',
            yaxis_title='Metric'
        )

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        fig.write_html(output_path)
        logger.info(f"Saved heatmap to {output_path}")

    except ImportError as e:
        logger.error(f"plotly not available: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error generating heatmap: {str(e)}")
        raise

def main() -> int:
    """Main entry point for visualization generation."""
    set_deterministic_seed(42)
    setup_logging("pipeline_log.txt")
    logger = get_logger()

    try:
        # Load similarity data
        input_path = Path("data/derived/yearly_similarity.csv")
        if not input_path.exists():
            logger.error(f"Similarity data not found: {input_path}")
            return 1

        import pandas as pd
        df = pd.read_csv(input_path)
        similarity_data = df.to_dict('records')

        # Generate plots
        generate_similarity_trend_plot(similarity_data)
        generate_genre_similarity_heatmap(similarity_data)

        logger.info("Visualization generation completed")
        return 0

    except Exception as e:
        logger.error(f"Visualization failed: {str(e)}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
