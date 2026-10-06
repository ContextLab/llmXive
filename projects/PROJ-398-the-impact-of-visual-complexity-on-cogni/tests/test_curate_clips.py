import os
import json
import tempfile
import shutil
import unittest
from pathlib import Path

# Import the module under test
from src.experiment.curate_clips import (
    curate_clips,
    get_video_info,
    meets_criteria,
    load_dataset_manifest,
    get_video_files,
    PROCESSED_CSV_PATH,
    CURATED_MANIFEST_PATH,
    DATASET_MANIFEST_PATH,
)

class TestCurateClips(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory structure mimicking the project layout
        self.temp_dir = Path(tempfile.mkdtemp())
        # Override global paths to point inside the temporary directory
        self.original_raw_dir = Path("data/stimuli/raw")
        self.original_processed_csv = PROCESSED_CSV_PATH
        self.original_curated_manifest = CURATED_MANIFEST_PATH
        self.original_dataset_manifest = DATASET_MANIFEST_PATH

        # Redirect paths
        globals()["RAW_CLIPS_DIR"] = self.temp_dir / "data/stimuli/raw"
        globals()["PROCESSED_CSV_PATH"] = self.temp_dir / "data/processed/curated_clips.csv"
        globals()["CURATED_MANIFEST_PATH"] = self.temp_dir / "data/metadata/curated_manifest.json"
        globals()["DATASET_MANIFEST_PATH"] = self.temp_dir / "data/metadata/dataset_manifest.json"

        # Ensure directories exist
        RAW_CLIPS_DIR.mkdir(parents=True, exist_ok=True)

        # Create a minimal fake dataset manifest (required by load_dataset_manifest)
        dataset_manifest = {
            "dataset_version": "v1.0",
            "source_url": "https://huggingface.co/datasets/video-conference-backgrounds",
            "checksum_manifest": {}
        }
        with DATASET_MANIFEST_PATH.open("w", encoding="utf-8") as fp:
            json.dump(dataset_manifest, fp)

        # Create a tiny valid video file using OpenCV (real video, not synthetic data)
        # The video will be 1 second long, 640x360 resolution, meeting the criteria.
        import cv2
        import numpy as np

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        video_path = RAW_CLIPS_DIR / "test_clip.mp4"
        out = cv2.VideoWriter(str(video_path), fourcc, 1.0, (640, 360))
        # Write a single black frame
        frame = np.zeros((360, 640, 3), dtype=np.uint8)
        out.write(frame)
        out.release()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_curate_clips_produces_outputs(self):
        # Run the curation
        curate_clips()

        # Verify CSV exists and contains the expected record
        self.assertTrue(PROCESSED_CSV_PATH.is_file())
        with PROCESSED_CSV_PATH.open("r", encoding="utf-8") as f:
            lines = f.read().strip().splitlines()
        # Header + one data line expected
        self.assertEqual(len(lines), 2)

        # Verify manifest exists and records correct provenance
        self.assertTrue(CURATED_MANIFEST_PATH.is_file())
        with CURATED_MANIFEST_PATH.open("r", encoding="utf-8") as f:
            manifest = json.load(f)
        self.assertEqual(manifest["source_dataset_version"], "v1.0")
        self.assertIn("filter_criteria", manifest)
        self.assertEqual(manifest["curated_count"], 1)

    def test_meets_criteria_logic(self):
        info = {"width": 800, "height": 600, "duration": 9.5}
        self.assertTrue(meets_criteria(info))
        info = {"width": 600, "height": 400, "duration": 5}
        self.assertFalse(meets_criteria(info))
        info = {"width": 640, "height": 360, "duration": 11}
        self.assertFalse(meets_criteria(info))

    def test_get_video_info_returns_expected_keys(self):
        video_path = next(RAW_CLIPS_DIR.iterdir())
        info = get_video_info(video_path)
        for key in ["width", "height", "duration", "fps", "frame_count"]:
            self.assertIn(key, info)

    def test_load_dataset_manifest_reads_correctly(self):
        manifest = load_dataset_manifest()
        self.assertEqual(manifest["dataset_version"], "v1.0")
        self.assertEqual(manifest["source_url"], "https://huggingface.co/datasets/video-conference-backgrounds")

    def test_get_video_files_finds_created_clip(self):
        files = get_video_files()
        self.assertEqual(len(files), 1)
        self.assertTrue(str(files[0]).endswith(".mp4"))

if __name__ == "__main__":
    unittest.main()