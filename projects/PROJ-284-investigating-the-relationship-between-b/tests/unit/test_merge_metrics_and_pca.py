import os
import pandas as pd
from pathlib import Path

from analysis.correlations import merge_metrics_and_pca, run_pca_analysis

def test_merge_metrics_and_pca(tmp_path: Path):
    """
    Create synthetic but realistic metric and PCA files, run the merge
    function, and verify that the resulting CSV contains the expected
    columns and number of rows.
    """
    # Create a fake metrics CSV with a subject_id column
    metrics_df = pd.DataFrame({
        "subject_id": [1, 2, 3],
        "modularity": [0.3, 0.35, 0.32],
        "global_efficiency": [0.45, 0.44, 0.46],
        "participation_coef": [0.2, 0.22, 0.21],
        "within_module_degree": [1.1, 1.0, 1.2],
    })
    metrics_path = tmp_path / "metrics.csv"
    metrics_df.to_csv(metrics_path, index=False)

    # Run PCA on the same data to generate a scores file
    pca_scores_path = tmp_path / "factor_scores.csv"
    pca_loadings_path = tmp_path / "pca_loadings.csv"
    run_pca_analysis(metrics_df, pca_loadings_path, pca_scores_path, n_components=2)

    # Destination for merged output
    output_path = tmp_path / "full_metrics.csv"

    # Execute the merge
    merge_metrics_and_pca(metrics_path, pca_scores_path, output_path)

    # Verify output exists
    assert output_path.is_file()

    # Load and check columns
    merged_df = pd.read_csv(output_path)
    expected_columns = [
        "subject_id",
        "modularity",
        "global_efficiency",
        "participation_coef",
        "within_module_degree",
        "pca_factor_1",
        "pca_factor_2",
    ]
    assert list(merged_df.columns) == expected_columns
    # Should have the same number of rows as the original metrics
    assert len(merged_df) == len(metrics_df)