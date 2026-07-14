import unittest
import tempfile
import shutil
import yaml
from pathlib import Path

# Import the functions from the script we just implemented
from scripts.update_manifest import (
    should_include_file,
    get_all_artifacts,
    get_artifact_metadata,
    update_manifest,
)
from utils.io import compute_checksum


class TestUpdateManifest(unittest.TestCase):
    """Integration tests for the manifest‑updating script."""

    def setUp(self):
        # Create a temporary directory that mimics a small repository
        self.repo_dir = Path(tempfile.mkdtemp())
        # Create the expected top‑level artifact directories
        for sub in ("data/raw", "data/processed", "models", "results", "state"):
            (self.repo_dir / sub).mkdir(parents=True, exist_ok=True)

        # Populate some dummy artifact files
        self.file_paths = [
            self.repo_dir / "data/raw/genomic_vcf.json",
            self.repo_dir / "data/processed/filtered.csv",
            self.repo_dir / "models/model.pkl",
            self.repo_dir / "results/permutation_results.json",
            self.repo_dir / "state/PROJ-475-predicting-plant-defense-compound-produc.yaml",
        ]
        for p in self.file_paths:
            p.write_text("dummy content for " + p.name)

        # Write an initial manifest with placeholder checksums
        self.manifest_path = self.repo_dir / "data" / "manifest.yaml"
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        initial_manifest = {
            "version": "1.0",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z",
            "artifacts": [
                {
                    "path": "data/raw/genomic_vcf.json",
                    "type": "raw_data",
                    "description": "Genomic variant data in JSON format",
                    "checksum": "sha256:placeholder",
                    "generated_by": "code/data/ingestion.py",
                }
            ],
        }
        with self.manifest_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(initial_manifest, f)

    def tearDown(self):
        shutil.rmtree(self.repo_dir)

    def test_should_include_file(self):
        # Files inside the recognised directories should be included
        self.assertTrue(should_include_file(Path("data/raw/genomic_vcf.json")))
        self.assertTrue(should_include_file(Path("models/model.pkl")))
        # The manifest itself must be excluded
        self.assertFalse(should_include_file(Path("data/manifest.yaml")))
        # Files outside the top‑level dirs are ignored
        self.assertFalse(should_include_file(Path("README.md")))

    def test_get_all_artifacts(self):
        artifacts = get_all_artifacts(self.repo_dir)
        expected = {str(p.relative_to(self.repo_dir)) for p in self.file_paths}
        self.assertEqual(set(str(a) for a in artifacts), expected)

    def test_update_manifest_refreshes_checksums_and_adds_missing(self):
        # Run the updater on the temporary repo
        update_manifest(
            manifest_path=self.manifest_path,
            repo_root=self.repo_dir,
        )

        # Load the updated manifest
        with self.manifest_path.open("r", encoding="utf-8") as f:
            updated = yaml.safe_load(f)

        # All files should now be present
        manifest_paths = {entry["path"] for entry in updated["artifacts"]}
        expected_paths = {str(p.relative_to(self.repo_dir)) for p in self.file_paths}
        self.assertEqual(manifest_paths, expected_paths)

        # Checksums must match the real file contents
        for entry in updated["artifacts"]:
            file_path = self.repo_dir / entry["path"]
            expected_checksum = compute_checksum(file_path)
            self.assertEqual(entry["checksum"], expected_checksum)

    def test_get_artifact_metadata_produces_valid_structure(self):
        meta = get_artifact_metadata(Path("data/raw/genomic_vcf.json"))
        self.assertIn("path", meta)
        self.assertIn("type", meta)
        self.assertIn("checksum", meta)
        self.assertEqual(meta["path"], "data/raw/genomic_vcf.json")
        # The type inference for a raw data file should be 'raw_data'
        self.assertEqual(meta["type"], "raw_data")


if __name__ == "__main__":
    unittest.main()
