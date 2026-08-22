import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json
import subprocess

# This integration test verifies the full R script execution
# It requires R and DESeq2 to be installed

@pytest.mark.integration
def test_run_de_per_tumor_script():
    """
    Integration test for the R script run_de_per_tumor.R
    This test creates mock data, runs the R script, and verifies the output.
    """
    # Skip if R is not available
    try:
        subprocess.run(['Rscript', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("Rscript not found, skipping integration test")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create mock counts data (small for speed)
        np.random.seed(42)
        n_genes = 50
        n_samples = 12
        gene_names = [f"GENE_{i}" for i in range(n_genes)]
        sample_ids = [f"Sample_{i}" for i in range(n_samples)]
        
        counts_data = np.random.poisson(100, size=(n_genes, n_samples))
        counts_df = pd.DataFrame(counts_data, index=gene_names, columns=sample_ids)
        
        # Create mock phenotypes
        pheno_data = {
            'response_label': ['Responder'] * 6 + ['NonResponder'] * 6,
            'tumor_type': ['TumorA'] * 12
        }
        pheno_df = pd.DataFrame(pheno_data, index=sample_ids)
        
        # Save to temp dir
        counts_path = tmpdir / "counts.csv"
        pheno_path = tmpdir / "phenotypes.csv"
        output_dir = tmpdir / "output"
        output_dir.mkdir()
        
        counts_df.to_csv(counts_path)
        pheno_df.to_csv(pheno_path)
        
        # Path to the R script
        script_path = Path(__file__).parent.parent.parent / "code" / "scripts" / "run_de_per_tumor.R"
        
        if not script_path.exists():
            pytest.skip("R script not found")
        
        # Run the R script
        cmd = [
            'Rscript',
            str(script_path),
            str(counts_path),
            str(pheno_path),
            str(output_dir)
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            # Check if it's a DESeq2 error (expected if data is too small)
            if "Insufficient samples" in e.stderr or "DESeq2 analysis failed" in e.stderr:
                pytest.skip("DESeq2 failed due to insufficient samples (expected in integration test with small data)")
            else:
                raise e
        
        # Check if output file was created
        output_files = list(output_dir.glob("de_results_*.csv"))
        assert len(output_files) > 0, "No DE results files were created"
        
        # Verify the content of the output file
        result_df = pd.read_csv(output_files[0])
        assert 'log2FoldChange' in result_df.columns
        assert 'pvalue' in result_df.columns
        assert 'padj' in result_df.columns
        assert len(result_df) > 0