"""
Integration test for the hash utilities to ensure they work correctly
with the pipeline's artifact generation flow.
"""
import json
import tempfile
from pathlib import Path
import pytest
from code.utils.hash import calculate_sha256, generate_manifest, verify_manifest

@pytest.fixture
def pipeline_artifacts_dir():
    """Create a temporary directory structure mimicking pipeline outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        data_dir = root / "data"
        data_dir.mkdir()
        
        # Create simulated pipeline artifacts
        (data_dir / "sample_01.bam").write_bytes(b"BAM_HEADER_DATA_1")
        (data_dir / "sample_02.bam").write_bytes(b"BAM_HEADER_DATA_2")
        (data_dir / "psi_table.tsv").write_bytes("event_id\tPSI\nES1\t0.5")
        (data_dir / "pipeline.log").write_bytes("2023-10-01 Step 1 complete\n")
        
        yield root

def test_full_pipeline_manifest_flow(pipeline_artifacts_dir):
    """
    Test the full flow: generate manifest for pipeline artifacts,
    verify integrity, modify a file, and verify failure.
    """
    artifacts = [
        pipeline_artifacts_dir / "data" / "sample_01.bam",
        pipeline_artifacts_dir / "data" / "sample_02.bam",
        pipeline_artifacts_dir / "data" / "psi_table.tsv",
        pipeline_artifacts_dir / "data" / "pipeline.log",
    ]
    
    manifest_path = pipeline_artifacts_dir / "artifacts_manifest.json"
    
    # 1. Generate manifest
    manifest = generate_manifest(artifacts, output_path=manifest_path)
    assert manifest_path.exists()
    assert len(manifest) == 4
    
    # 2. Verify integrity
    assert verify_manifest(manifest_path) is True
    
    # 3. Corrupt a file
    (pipeline_artifacts_dir / "data" / "sample_01.bam").write_bytes(b"CORRUPTED_DATA")
    
    # 4. Verify should fail
    assert verify_manifest(manifest_path) is False
    
    # 5. Restore file
    (pipeline_artifacts_dir / "data" / "sample_01.bam").write_bytes(b"BAM_HEADER_DATA_1")
    
    # 6. Verify should pass again
    assert verify_manifest(manifest_path) is True
