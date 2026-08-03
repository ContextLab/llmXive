"""
Unit tests for generate_assets.py

Verifies:
  1. Images are created with correct dimensions
  2. Manifest file is created with correct structure
  3. SHA256 hashes in manifest match actual files
  4. Text is present in images (basic check)
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest import TestCase

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from scripts.generate_assets import (
    get_project_root,
    ensure_dirs,
    create_technical_diagram,
    compute_sha256,
    generate_assets
)


class TestGenerateAssets(TestCase):
    """Tests for asset generation functionality."""

    def test_create_technical_diagram_dimensions(self):
        """Verify images are created with correct size."""
        img = create_technical_diagram(0)
        self.assertEqual(img.size, (336, 336))
        self.assertEqual(img.mode, "L")  # Grayscale

    def test_create_technical_diagram_content(self):
        """Verify images have non-uniform content (not blank)."""
        img = create_technical_diagram(0)
        pixels = list(img.getdata())
        # Check that not all pixels are the same (white background)
        unique_values = set(pixels)
        self.assertGreater(len(unique_values), 1, "Image appears to be blank/uniform")

    def test_compute_sha256_consistency(self):
        """Verify SHA256 computation is consistent."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test data")
            temp_path = f.name

        try:
            hash1 = compute_sha256(Path(temp_path))
            hash2 = compute_sha256(Path(temp_path))
            self.assertEqual(hash1, hash2)
            # Verify it's a valid hex string
            self.assertEqual(len(hash1), 64)
            int(hash1, 16)  # Should not raise
        finally:
            os.unlink(temp_path)

    def test_ensure_dirs_creates_directory(self):
        """Verify ensure_dirs creates the assets directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            assets_dir = ensure_dirs(root)
            self.assertTrue(assets_dir.exists())
            self.assertEqual(assets_dir.name, "assets")

    def test_generate_assets_creates_manifest(self):
        """Verify generate_assets creates a valid manifest.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            entries = generate_assets(root, count=3)

            # Check manifest exists
            manifest_path = root / "data" / "assets" / "manifest.json"
            self.assertTrue(manifest_path.exists())

            # Check manifest content
            with open(manifest_path) as f:
                manifest = json.load(f)

            self.assertEqual(manifest["generated_count"], 3)
            self.assertIn("entries", manifest)
            self.assertEqual(len(manifest["entries"]), 3)

            # Check entry structure
            for entry in manifest["entries"]:
                self.assertIn("filename", entry)
                self.assertIn("sha256", entry)
                self.assertIn("path", entry)
                self.assertIn("size_px", entry)

    def test_generate_assets_creates_images(self):
        """Verify generate_assets creates the image files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            generate_assets(root, count=3)

            assets_dir = root / "data" / "assets"
            for i in range(3):
                filename = f"img_{i:02d}.png"
                filepath = assets_dir / filename
                self.assertTrue(filepath.exists(), f"{filename} not created")
                self.assertGreater(filepath.stat().st_size, 0, f"{filename} is empty")

    def test_manifest_hashes_match_files(self):
        """Verify SHA256 hashes in manifest match actual file hashes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            generate_assets(root, count=3)

            manifest_path = root / "data" / "assets" / "manifest.json"
            with open(manifest_path) as f:
                manifest = json.load(f)

            for entry in manifest["entries"]:
                filepath = root / entry["path"]
                actual_hash = compute_sha256(filepath)
                self.assertEqual(
                    entry["sha256"],
                    actual_hash,
                    f"Hash mismatch for {entry['filename']}"
                )
