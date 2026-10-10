"""
Integration test for end-to-end scVelo run on GSE136103.
Verifies that velocity_graph.h5ad is produced with required fields.
"""
import pytest
import subprocess
import sys
from pathlib import Path

def test_end_to_end_scvelo_run():
    """
    Run the velocity.py script on GSE136103 and verify outputs.
    """
    # Paths
    input_file = Path("data/processed/GSE136103_processed.h5ad")
    output_file = Path("data/results/velocity_graph.h5ad")
    velocity_script = Path("code/velocity.py")

    # We fail if the input data is missing because T004 depends on T003
    if not input_file.exists():
        pytest.fail(f"Required input file {input_file} is missing. Preprocessing (T003) must run first.")
    
    if not velocity_script.exists():
        pytest.fail(f"Script {velocity_script} not found.")

    # Run the velocity script
    try:
        result = subprocess.run(
            [sys.executable, str(velocity_script), "--input", str(input_file), "--output", str(output_file)],
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        pytest.fail(f"Velocity script failed with return code {e.returncode}: {e.stderr}")

    # Verify output file exists
    assert output_file.exists(), f"Output file {output_file} was not created."
    assert output_file.stat().st_size > 0, "Output file is empty."

    # Verify required fields
    try:
        import scanpy as sc
        import anndata as ad
      
        adata = ad.read_h5ad(str(output_file))
        
        # 1. Check for spliced and unspliced layers
        assert "spliced" in adata.layers, "Spliced layer missing from output."
        assert "unspliced" in adata.layers, "Unspliced layer missing from output."
        
        # 2. Check for velocity
        # scVelo stores velocity in adata.layers['velocity']
        assert "velocity" in adata.layers, "Velocity layer missing from output."
        
        # 3. Check for pseudotime
        # Our script maps latent_time -> pseudotime in obs
        assert "pseudotime" in adata.obs, "Pseudotime missing from adata.obs."
        
        # Verify pseudotime is numeric and not all NaN
        import numpy as np
        assert np.all(np.isfinite(adata.obs["pseudotime"])), "Pseudotime contains non-finite values."
        assert not np.all(adata.obs["pseudotime"] == 0), "Pseudotime is all zeros."

    except ImportError:
        pytest.fail("Required libraries (scanpy, anndata) not installed for verification.")
    except Exception as e:
        pytest.fail(f"Failed to verify output fields: {e}")