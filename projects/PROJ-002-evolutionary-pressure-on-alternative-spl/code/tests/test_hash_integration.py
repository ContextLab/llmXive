"""
Integration tests for the hashing utilities (T006).
Verifies the full flow of manifest generation and verification
including external artifacts like phylogenetic trees.
"""
import json
import tempfile
from pathlib import Path
import pytest

from code.utils.hash import calculate_sha256, generate_manifest, verify_manifest


@pytest.fixture
def pipeline_artifacts_dir():
    """Create a mock pipeline directory structure with artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        data_dir = base / "data"
        data_dir.mkdir()

        # Create mock pipeline artifacts
        bam_file = data_dir / "sample1.bam"
        bam_file.write_bytes(b"FAKE_BAM_DATA")

        psi_file = data_dir / "psi_table.tsv"
        psi_file.write_text("gene_id\tevent_id\tPSI\nENSG001\tSE1\t0.5\n")

        tree_file = base / "primate_tree.nwk"
        tree_file.write_text("(Human:1.0, Chimp:1.0);")

        yield {
            "base": base,
            "bam": bam_file,
            "psi": psi_file,
            "tree": tree_file
        }


def test_full_pipeline_manifest_flow(pipeline_artifacts_dir):
    """
    Test the full flow:
    1. Generate manifest for pipeline artifacts (BAM, PSI)
    2. Include external artifact (phylogenetic tree)
    3. Verify the manifest
    4. Corrupt a file and verify failure
    """
    base = pipeline_artifacts_dir["base"]
    artifacts = [pipeline_artifacts_dir["bam"], pipeline_artifacts_dir["psi"]]
    external = {"primate_tree": pipeline_artifacts_dir["tree"]}
    manifest_path = base / "artifacts_manifest.json"

    # Step 1 & 2: Generate manifest
    manifest = generate_manifest(
        file_paths=artifacts,
        output_path=manifest_path,
        include_external=external
    )

    assert manifest_path.exists()
    assert "artifacts" in manifest
    assert "external_artifacts" in manifest
    assert "primate_tree" in manifest["external_artifacts"]

    # Step 3: Verify success
    assert verify_manifest(manifest_path) is True

    # Step 4: Corrupt a file
    pipeline_artifacts_dir["psi"].write_text("CORRUPTED_DATA")

    # Verification should fail
    assert verify_manifest(manifest_path) is False
