"""
Integration tests for manifest generation (T014).
Verifies end-to-end manifest creation and validation workflow.
"""
import json
import tempfile
from pathlib import Path
from unittest import TestCase
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.utils.manifest import (
    generate_manifest,
    validate_manifest,
    compute_file_hash
)

class TestManifestIntegration(TestCase):
    """Integration tests for manifest generation workflow."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.output_dir = self.temp_dir / "output"
        self.output_dir.mkdir()
        
        # Create realistic audit artifacts
        self.audit_report = self.output_dir / "audit_report.json"
        self.summary_report = self.output_dir / "summary_report.csv"
        self.power_analysis = self.output_dir / "power_analysis.json"
        self.manifest_path = self.output_dir / "manifest.json"
        
        # Write test data
        self.audit_report.write_text(json.dumps({
            "total_summaries": 100,
            "inconsistent_count": 5,
            "records": []
        }))
        
        self.summary_report.write_text(
            "total_summaries,inconsistent_count,inconsistent_rate\n100,5,0.05\n"
        )
        
        self.power_analysis.write_text(json.dumps({
            "sample_size": 300,
            "power": 0.8,
            "alpha": 0.05
        }))

    def tearDown(self):
        """Clean up test files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_manifest_workflow(self):
        """Test complete manifest generation and validation workflow."""
        artifacts = [self.audit_report, self.summary_report, self.power_analysis]
        
        # Generate manifest
        manifest = generate_manifest(
            artifact_paths=artifacts,
            output_path=self.manifest_path,
            include_metadata=True
        )
        
        # Verify manifest was created
        self.assertTrue(self.manifest_path.exists())
        
        # Validate manifest
        is_valid = validate_manifest(self.manifest_path, self.output_dir)
        self.assertTrue(is_valid)

    def test_manifest_after_file_modification(self):
        """Test that manifest validation detects file modifications."""
        artifacts = [self.audit_report, self.summary_report]
        
        # Generate manifest
        generate_manifest(
            artifact_paths=artifacts,
            output_path=self.manifest_path,
            include_metadata=False
        )
        
        # Validate initially
        self.assertTrue(validate_manifest(self.manifest_path, self.output_dir))
        
        # Modify a file
        self.audit_report.write_text(json.dumps({"modified": True}))
        
        # Validation should now fail
        self.assertFalse(validate_manifest(self.manifest_path, self.output_dir))

    def test_manifest_with_realistic_audit_artifacts(self):
        """
        Integration test: Verify manifest correctly handles realistic audit artifacts.
        Ensures T014 works with actual pipeline outputs.
        """
        # Create realistic artifacts
        artifacts = [self.audit_report, self.summary_report, self.power_analysis]
        
        # Generate manifest
        manifest = generate_manifest(
            artifact_paths=artifacts,
            output_path=self.manifest_path,
            include_metadata=True
        )
        
        # Verify all artifacts are included
        self.assertEqual(len(manifest["artifacts"]), 3)
        
        # Verify each artifact has correct hash
        for artifact_path in artifacts:
            relative_path = str(artifact_path.relative_to(self.output_dir.parent))
            self.assertIn(relative_path, manifest["artifacts"])
            
            entry = manifest["artifacts"][relative_path]
            expected_hash = compute_file_hash(artifact_path)
            self.assertEqual(entry["sha256"], expected_hash)
            
            # Verify metadata
            self.assertIn("size_bytes", entry)
            self.assertIn("modified_at", entry)
            self.assertGreater(entry["size_bytes"], 0)

    def test_manifest_validation_with_missing_artifact(self):
        """Test validation fails gracefully when an artifact is missing."""
        artifacts = [self.audit_report, self.summary_report]
        
        generate_manifest(
            artifact_paths=artifacts,
            output_path=self.manifest_path,
            include_metadata=False
        )
        
        # Remove one artifact
        self.summary_report.unlink()
        
        # Validation should return False
        is_valid = validate_manifest(self.manifest_path, self.output_dir)
        self.assertFalse(is_valid)

    def test_manifest_path_resolution(self):
        """Test that manifest correctly resolves relative paths."""
        artifacts = [self.audit_report, self.summary_report]
        
        manifest = generate_manifest(
            artifact_paths=artifacts,
            output_path=self.manifest_path,
            include_metadata=False
        )
        
        # Check that paths are relative to the project root
        for path_str, entry in manifest["artifacts"].items():
            # Path should not be absolute
            self.assertFalse(Path(path_str).is_absolute())
            # Path should be under output/
            self.assertTrue(path_str.startswith("output/"))