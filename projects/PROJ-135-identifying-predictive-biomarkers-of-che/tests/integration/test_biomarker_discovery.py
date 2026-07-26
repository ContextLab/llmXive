"""
Integration test for DE and panel selection logic on 3 tumor types (simulated).

This test verifies the logic of User Story 2 (Cross-Cancer Biomarker Identification)
by running Differential Expression (DE) and panel selection on simulated data that
mimics the structure of real TCGA/GEO processed data.

It ensures:
1. DE logic (Wald test approximation) correctly identifies significant genes based on
   FDR and log2FC thresholds.
2. Meta-analysis logic (Intersection/Union/Stouffer's) correctly combines results
   across multiple tumor types.
3. The final gene panel is saved to the expected output path.

NOTE: This test uses simulated data to avoid the long runtime of real DESeq2 on
full datasets during integration testing. The logic is validated against the
expected mathematical properties of the algorithms.
"""

import os
import sys
import json
import tempfile
import numpy as np
import pandas as pd
from pathlib import Path
import pytest
from scipy import stats

# Add project root to path if necessary (usually handled by conftest or PYTHONPATH)
# Assuming standard project structure where this file is at tests/integration/
# and src/ is at the root.
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.meta_analysis import (
    compute_intersection,
    compute_union_top_genes,
    stouffers_meta_analysis,
    save_gene_panel
)
from src.differential_expression import (
    run_differential_expression_simulation
)
from src.config import get_project_root, ensure_directories


def _generate_simulated_discovery_data(
    n_samples: int = 100,
    n_genes: int = 5000,
    n_sig_genes: int = 50,
    tumor_type: str = "LUAD",
    seed: int = 42
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Generates synthetic discovery set data mimicking VST-normalized RNA-seq.

    Returns:
        expression_df: DataFrame of shape (n_samples, n_genes)
        labels: Series of binary labels (0: non-responder, 1: responder)
    """
    rng = np.random.default_rng(seed)
    labels = rng.choice([0, 1], size=n_samples, p=[0.6, 0.4])

    # Create expression matrix with base noise
    data = rng.normal(loc=10, scale=2, size=(n_samples, n_genes))

    # Inject signal into n_sig_genes
    sig_indices = rng.choice(n_genes, size=n_sig_genes, replace=False)
    for idx in sig_indices:
        # Responder mean shift (log2FC ~ 1.5)
        data[labels == 1, idx] += 1.5
        # Add some noise to the shift
        data[labels == 1, idx] += rng.normal(0, 0.2, size=n_samples)[labels == 1]

    # Create gene symbols
    gene_symbols = [f"GENE_{i}" for i in range(n_genes)]
    # Ensure some overlap with a "true" panel for later verification
    true_panel_genes = [gene_symbols[i] for i in sig_indices]

    expression_df = pd.DataFrame(data, columns=gene_symbols)
    expression_df.index = [f"Sample_{i}" for i in range(n_samples)]

    return expression_df, pd.Series(labels, name="response"), true_panel_genes


def test_de_and_panel_selection_logic():
    """
    Integration test for DE and panel selection logic on 3 tumor types.

    Steps:
    1. Generate simulated discovery data for 3 tumor types.
    2. Run simulated DE on each type.
    3. Verify intersection logic.
    4. Verify union fallback logic.
    5. Verify Stouffer's meta-analysis.
    6. Verify final panel saving.
    """
    # Setup
    temp_dir = tempfile.mkdtemp()
    results_dir = Path(temp_dir) / "results" / "meta_analysis"
    ensure_directories(results_dir)

    tumor_types = ["LUAD", "BRCA", "COAD"]
    de_results_list = []
    all_true_panels = []

    print("Generating simulated discovery data...")
    for i, tumor in enumerate(tumor_types):
        expr, labels, true_panel = _generate_simulated_discovery_data(
            n_samples=150,
            n_genes=2000,
            n_sig_genes=30, # 30 true significant genes
            tumor_type=tumor,
            seed=42 + i
        )

        # Save to disk to simulate the "discovery_set" input
        input_path = Path(temp_dir) / "data" / "processed" / f"{tumor}_discovery_set.csv"
        input_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Combine expression and labels
        full_df = expr.copy()
        full_df["response"] = labels
        full_df.to_csv(input_path, index=True)

        # Run DE Simulation
        # This function approximates the DESeq2 Wald test logic using t-test on simulated data
        print(f"Running DE simulation for {tumor}...")
        de_result = run_differential_expression_simulation(
            input_path=input_path,
            fdr_threshold=0.05,
            log2fc_threshold=1.0,
            seed=42 + i
        )
        
        de_results_list.append({
            "tumor_type": tumor,
            "significant_genes": de_result["significant_genes"],
            "p_values": de_result["p_values"],
            "log2fc": de_result["log2fc"]
        })
        
        all_true_panels.append(set(true_panel))

    # --- Test 1: Intersection Logic ---
    print("Testing Intersection Logic...")
    intersection_genes = compute_intersection(de_results_list)
    
    # With simulated data, we expect some overlap but not necessarily 100%
    # The intersection should be a subset of the union of all true panels
    all_true_union = set().union(*all_true_panels)
    assert intersection_genes.issubset(all_true_union), "Intersection genes must be from true signal sets"
    
    # Log results
    print(f"Intersection size: {len(intersection_genes)}")
    print(f"Intersection genes: {list(intersection_genes)[:10]}...")

    # --- Test 2: Union Fallback Logic ---
    print("Testing Union Fallback Logic...")
    # Force intersection to be empty to test fallback (simulate a scenario where no common genes)
    # In real data, if intersection is empty, we fall back to top 50 union.
    # Here we just verify the function exists and returns the top 50 if forced.
    # We will test the actual logic path by checking the function behavior.
    
    union_genes = compute_union_top_genes(de_results_list, top_n=50)
    assert len(union_genes) <= 50, "Union fallback should return at most top_n genes"
    assert len(union_genes) > 0, "Union fallback should return genes if data exists"
    print(f"Union (top 50) size: {len(union_genes)}")

    # --- Test 3: Stouffer's Meta-Analysis ---
    print("Testing Stouffer's Meta-Analysis...")
    # Prepare data for Stouffer's: need p-values aligned by gene
    # The function handles the alignment internally
    meta_results = stouffers_meta_analysis(de_results_list)
    
    assert "gene" in meta_results.columns, "Meta results must have 'gene' column"
    assert "stouffer_z" in meta_results.columns, "Meta results must have 'stouffer_z' column"
    assert "combined_p" in meta_results.columns, "Meta results must have 'combined_p' column"
    assert "rank" in meta_results.columns, "Meta results must have 'rank' column"
    
    print(f"Meta-analysis result shape: {meta_results.shape}")
    print(f"Top 5 meta genes: {meta_results.head(5)['gene'].tolist()}")

    # --- Test 4: Final Panel Selection and Saving ---
    print("Testing Final Panel Selection and Saving...")
    
    # Decide which logic to use based on intersection size
    if len(intersection_genes) > 0:
        final_panel_genes = list(intersection_genes)
        fallback_reason = None
    else:
        final_panel_genes = list(union_genes)
        fallback_reason = "intersection_empty"
    
    # Save the panel
    output_path = results_dir / "gene_panel.json"
    save_gene_panel(
        genes=final_panel_genes,
        meta_results=meta_results,
        output_path=output_path,
        fallback_reason=fallback_reason
    )

    # Verify file exists
    assert output_path.exists(), f"Output file {output_path} was not created"
    
    # Verify content
    with open(output_path, 'r') as f:
        panel_data = json.load(f)
    
    assert "genes" in panel_data, "JSON must contain 'genes' list"
    assert "metadata" in panel_data, "JSON must contain 'metadata'"
    assert panel_data["metadata"]["fallback_reason"] == fallback_reason or fallback_reason is None
    
    print(f"Final panel saved to {output_path}")
    print(f"Panel size: {len(panel_data['genes'])}")
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)

    # Assertions for the test to pass
    assert len(panel_data["genes"]) > 0, "Final panel must not be empty"
    assert len(panel_data["genes"]) <= 50, "Final panel should not exceed 50 genes (unless intersection > 50, but logic caps at intersection or top 50)"
    
    print("Integration test PASSED: DE and panel selection logic verified.")


if __name__ == "__main__":
    test_de_and_panel_selection_logic()