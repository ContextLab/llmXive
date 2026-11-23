import json
import tempfile
from pathlib import Path
import pytest

from code.utils.hash import calculate_sha256, generate_manifest, verify_manifest

@pytest.fixture
def pipeline_artifacts_dir():
    """Create a temporary directory structure simulating pipeline outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        # Create subdirectories
        (base / "bam").mkdir()
        (base / "psi").mkdir()
        (base / "results").mkdir()

        # Create sample files
        (base / "bam" / "sample1.bam").write_bytes(b"BAM_HEADER_SAMPLE1")
        (base / "bam" / "sample2.bam").write_bytes(b"BAM_HEADER_SAMPLE2")
        (base / "psi" / "psi_table.tsv").write_text("gene\tevent\tpsi\nG1\tE1\t0.5")
        (base / "results" / "enrichment.tsv").write_text("lineage\tp_value\nHomo\t0.01")

        # Create an external input file (e.g., phylogenetic tree)
        (base / "primate_tree.nwk").write_text("(Human:1.0, Chimp:1.0);")

        yield base

def test_full_pipeline_manifest_flow(pipeline_artifacts_dir):
    """Test generating a manifest for all pipeline artifacts and verifying it."""
    base_dir = pipeline_artifacts_dir

    # Define files to hash (simulating what the pipeline would do)
    files_to_hash = [
        base_dir / "bam" / "sample1.bam",
        base_dir / "bam" / "sample2.bam",
        base_dir / "psi" / "psi_table.tsv",
        base_dir / "results" / "enrichment.tsv",
        base_dir / "primate_tree.nwk"  # External input artifact
    ]

    manifest_path = base_dir / "artifacts_manifest.json"

    # Generate manifest
    manifest = generate_manifest(files_to_hash, manifest_path)

    # Verify manifest was created
    assert manifest_path.exists()

    # Verify content
    assert len(manifest["files"]) == 5

    # Verify specific files are present
    assert "bam/sample1.bam" in manifest["files"]
    assert "psi/psi_table.tsv" in manifest["files"]
    assert "primate_tree.nwk" in manifest["files"]

    # Verify hashes are correct by recalculating
    for rel_path, entry in manifest["files"].items():
        file_path = base_dir / rel_path
        if file_path.exists():
            calculated_hash = calculate_sha256(file_path)
            assert calculated_hash == entry["sha256"], f"Hash mismatch for {rel_path}"

    # Test verification function
    assert verify_manifest(manifest_path) is True

    # Test verification failure if file is modified
    (base_dir / "psi" / "psi_table.tsv").write_text("MODIFIED CONTENT")
    assert verify_manifest(manifest_path) is False