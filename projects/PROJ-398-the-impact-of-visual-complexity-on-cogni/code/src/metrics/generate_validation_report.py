import os
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, fisher_exact
from scipy.stats import norm
from src.config import get_relative_path

def load_human_ratings() -> pd.DataFrame:
    """
    Load human ratings from the CSV file produced by the pilot study.

    Returns:
        pd.DataFrame with columns ['image_id', 'participant_id', 'complexity_score']
    """
    ratings_path = get_relative_path(os.path.join('data', 'measurements', 'human_ratings.csv'))
    if not ratings_path.is_file():
        raise FileNotFoundError(f"Human ratings file not found at {ratings_path}")
    df = pd.read_csv(ratings_path)
    expected_cols = {'image_id', 'participant_id', 'complexity_score'}
    if not expected_cols.issubset(df.columns):
        raise ValueError(f"Human ratings CSV must contain columns {expected_cols}")
    return df

def load_metrics() -> pd.DataFrame:
    """
    Load automated visual‑complexity metrics.

    Returns:
        pd.DataFrame with at least columns ['image_id', 'entropy']
    """
    metrics_path = get_relative_path(os.path.join('data', 'processed', 'metrics.csv'))
    if not metrics_path.is_file():
        raise FileNotFoundError(f"Metrics file not found at {metrics_path}")
    df = pd.read_csv(metrics_path)
    expected_cols = {'image_id', 'entropy'}
    if not expected_cols.issubset(df.columns):
        raise ValueError(f"Metrics CSV must contain columns {expected_cols}")
    return df

def compute_correlation(human_df: pd.DataFrame, metrics_df: pd.DataFrame):
    """
    Compute Pearson correlation between average human complexity scores and
    the automated entropy metric.

    Returns:
        r (float): Pearson correlation coefficient
        p (float): two‑tailed p‑value
        n (int): number of paired observations
    """
    # Average human rating per image
    human_avg = human_df.groupby('image_id')['complexity_score'].mean().reset_index()
    merged = pd.merge(human_avg, metrics_df[['image_id', 'entropy']], on='image_id', how='inner')
    if merged.empty:
        raise ValueError("No overlapping image IDs between human ratings and metrics.")
    r, p = pearsonr(merged['complexity_score'], merged['entropy'])
    n = len(merged)
    return r, p, n, merged

def create_scatter_plot(merged_df: pd.DataFrame, output_path: Path):
    """
    Create and save a scatter plot of human vs. automated scores.

    Args:
        merged_df: DataFrame containing 'complexity_score' and 'entropy' columns.
        output_path: Path where the PNG image will be saved.
    """
    plt.figure(figsize=(8, 6))
    plt.scatter(merged_df['complexity_score'], merged_df['entropy'], alpha=0.7)
    plt.title('Human Complexity Scores vs. Automated Entropy')
    plt.xlabel('Average Human Complexity Score')
    plt.ylabel('Entropy (Automated Metric)')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close()

def compute_confidence_interval(r: float, n: int, confidence: float = 0.95):
    """
    Compute the confidence interval for Pearson's r using Fisher's z‑transform.

    Args:
        r: Pearson correlation coefficient.
        n: Number of paired observations.
        confidence: Desired confidence level (default 0.95).

    Returns:
        (lower, upper): Tuple of lower and upper bounds for r.
    """
    if n <= 3:
        raise ValueError("At least 4 observations are required for a confidence interval.")
    # Fisher z transformation
    z = 0.5 * (np.log1p(r) - np.log1p(-r))
    se = 1 / np.sqrt(n - 3)
    z_crit = norm.ppf(0.5 + confidence / 2)
    lo_z, hi_z = z - z_crit * se, z + z_crit * se
    lo, hi = (np.tanh(lo_z), np.tanh(hi_z))
    return lo, hi

def write_markdown_report(r: float, p: float, ci_lower: float, ci_upper: float,
                         plot_path: Path, report_path: Path):
    """
    Write the markdown report summarising the pilot validation.

    Args:
        r: Pearson correlation coefficient.
        p: Two‑tailed p‑value.
        ci_lower / ci_upper: Confidence interval bounds.
        plot_path: Path to the scatter‑plot PNG (relative to the report).
        report_path: Destination path for the markdown file.
    """
    report_path.parent.mkdir(parents=True, exist_ok=True)
    relative_plot = plot_path.relative_to(report_path.parent)
    markdown = f"""# Pilot Validation Report

  This report summarises the relationship between human‑rated visual‑complexity scores
  and the automated entropy metric extracted from the stimulus images.

  ## Scatter Plot

  ![Human vs. Entropy]({relative_plot})

  ## Statistics

  * **Pearson correlation (r):** {r:.4f}
  * **Two‑tailed p‑value:** {p:.4e}
  * **95 % confidence interval for r:** [{ci_lower:.4f}, {ci_upper:.4f}]

  The plot visualises each image as a point where the x‑axis reflects the average
  human complexity rating and the y‑axis reflects the computed entropy.
  """
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(markdown)

def main():
    """
    End‑to‑end generation of the pilot validation report.
    """
    import numpy as np  # Imported here to keep the module import order clean
    # Load data
    human_df = load_human_ratings()
    metrics_df = load_metrics()

    # Compute correlation and obtain merged data for plotting
    r, p, n, merged = compute_correlation(human_df, metrics_df)

    # Compute 95 % confidence interval
    ci_lower, ci_upper = compute_confidence_interval(r, n)

    # Paths
    plot_path = get_relative_path(os.path.join('data', 'derived', 'pilot_validation_scatter.png'))
    report_path = get_relative_path(os.path.join('data', 'derived', 'pilot_validation_report.md'))

    # Generate artifacts
    create_scatter_plot(merged, plot_path)
    write_markdown_report(r, p, ci_lower, ci_upper, plot_path, report_path)

    print(f"Pilot validation report generated at {report_path}")

if __name__ == "__main__":
    main()