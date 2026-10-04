import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.experiment.curate_neutral import curate_neutral

class TestCurateNeutral(unittest.TestCase):
    """Validate that low‑complexity stimuli are correctly identified and copied."""

    def setUp(self):
        # Create a temporary directory structure mimicking the real data layout.
        self.temp_dir = Path(tempfile.mkdtemp())
        self.raw_dir = self.temp_dir / "data" / "stimuli" / "raw"
        self.neutral_dir = self.temp_dir / "data" / "stimuli" / "neutral"
        self.raw_dir.mkdir(parents=True, exist_ok=True)

        # Populate with a few tiny synthetic images.
        # The YOLO model will see them as having 0 objects.
        from PIL import Image

        for i in range(3):
            img_path = self.raw_dir / f"img_{i}.png"
            Image.new("RGB", (100, 100), color=(i * 40, i * 40, i * 40)).save(img_path)

        # Add a more complex image (a simple black‑white checkerboard) that YOLO
        # typically detects at least one object. This ensures the filter excludes it.
        complex_path = self.raw_dir / "complex.png"
        img = Image.new("RGB", (200, 200), "white")
        for x in range(0, 200, 20):
            for y in range(0, 200, 20):
                if (x // 20 + y // 20) % 2 == 0:
                    for dx in range(20):
                        for dy in range(20):
                            img.putpixel((x + dx, y + dy), (0, 0, 0))
        img.save(complex_path)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_neutral_stimuli_categorized(self):
        selected = curate_neutral(
            raw_dir=self.raw_dir,
            neutral_dir=self.neutral_dir,
            max_object_count=2,
        )
        # Expect the three simple images to be copied; the complex one should be omitted.
        self.assertEqual(len(selected), 3)
        for p in selected:
            self.assertTrue(p.is_file())
            self.assertTrue(p.parent.samefile(self.neutral_dir))

        # Ensure the complex image was not copied.
        self.assertFalse((self.neutral_dir / "complex.png").exists())

if __name__ == "__main__":
    unittest.main()