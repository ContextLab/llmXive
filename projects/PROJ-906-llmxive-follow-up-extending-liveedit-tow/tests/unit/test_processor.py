import os
import json
import tempfile
import pytest
from pathlib import Path
import numpy as np
import cv2

from data.processor import (
    ProcessedClip,
    generate_synthetic_mask,
    stratify_by_motion,
    process_video_clip,
    process_dataset_stratification,
    load_processed_clips,
)
from config import STRATIFICATION_THRESHOLDS

# Helper to create a dummy video file
def create_dummy_video(path: str, frames: int = 10, h: int = 100, w: int = 100):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    out = cv2.VideoWriter(
        path,
        cv2.VideoWriter_fourcc(*'mp4v'),
        10,
        (w, h)
    )
    for _ in range(frames):
        frame = np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)
        out.write(frame)
    out.release()
    return path

class TestStratificationLogic:
    """Tests for T013b: Stratify clips by motion complexity."""

    def test_stratification_static(self):
        """Test that low flow magnitude results in 'Static'."""
        # Thresholds are {0.5, 5.0}
        # < 0.5 -> Static
        category = stratify_by_motion("clip_001", 0.1)
        assert category == "Static"

    def test_stratification_slow_rigid(self):
        """Test that medium flow magnitude results in 'Slow Rigid'."""
        # 0.5 <= x < 5.0 -> Slow Rigid
        category = stratify_by_motion("clip_002", 1.5)
        assert category == "Slow Rigid"

    def test_stratification_fast_non_rigid(self):
        """Test that high flow magnitude results in 'Fast Non-Rigid'."""
        # >= 5.0 -> Fast Non-Rigid
        category = stratify_by_motion("clip_003", 10.0)
        assert category == "Fast Non-Rigid"

    def test_stratification_edge_case_low_threshold(self):
        """Test edge case: exactly 0.5 should be 'Slow Rigid' (higher category)."""
        # Edge case: 0.5 is the boundary.
        # Logic: if mag < 0.5 -> Static, else (>= 0.5) check next.
        # Since 0.5 is not < 0.5, it falls to 'Slow Rigid'.
        category = stratify_by_motion("clip_004", 0.5)
        assert category == "Slow Rigid"

    def test_stratification_edge_case_high_threshold(self):
        """Test edge case: exactly 5.0 should be 'Fast Non-Rigid' (higher category)."""
        # Edge case: 5.0 is the boundary.
        # Logic: if mag < 5.0 -> Slow Rigid, else (>= 5.0) -> Fast Non-Rigid.
        category = stratify_by_motion("clip_005", 5.0)
        assert category == "Fast Non-Rigid"

    def test_stratification_custom_thresholds(self):
        """Test stratification with custom thresholds."""
        custom_thresh = {1.0, 10.0}
        # 0.5 < 1.0 -> Static
        assert stratify_by_motion("c1", 0.5, custom_thresh) == "Static"
        # 5.0 >= 1.0 and < 10.0 -> Slow Rigid
        assert stratify_by_motion("c2", 5.0, custom_thresh) == "Slow Rigid"
        # 15.0 >= 10.0 -> Fast Non-Rigid
        assert stratify_by_motion("c3", 15.0, custom_thresh) == "Fast Non-Rigid"

class TestMaskGeneration:
    """Tests for T013a: Mask generation (prerequisite)."""

    def test_mask_generation_creates_file(self, tmp_path):
        video_path = create_dummy_video(str(tmp_path / "test.mp4"))
        mask_path = generate_synthetic_mask(video_path, str(tmp_path / "masks"))
        
        assert os.path.exists(mask_path)
        assert mask_path.endswith(".png")
        
        # Verify mask is binary (0 or 255)
        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        assert mask is not None
        assert np.all((mask == 0) | (mask == 255))

    def test_mask_dimensions_match_video(self, tmp_path):
        h, w = 200, 300
        video_path = create_dummy_video(str(tmp_path / "dims.mp4"), h=h, w=w)
        mask_path = generate_synthetic_mask(video_path, str(tmp_path / "masks"))
        
        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        assert mask.shape == (h, w)

class TestProcessedClip:
    """Tests for ProcessedClip data structure."""

    def test_processed_clip_initialization(self):
        clip = ProcessedClip(
            clip_id="test_001",
            path="/fake/path.mp4",
            mask_path="/fake/mask.png",
            motion_category="Static",
            flow_magnitude=0.1
        )
        assert clip.clip_id == "test_001"
        assert clip.motion_category == "Static"
        assert clip.flow_magnitude == 0.1

class TestDatasetStratification:
    """Tests for process_dataset_stratification."""

    def test_process_dataset_stratification_report(self, tmp_path):
        # Create dummy videos
        clip1 = create_dummy_video(str(tmp_path / "clip1.mp4"))
        clip2 = create_dummy_video(str(tmp_path / "clip2.mp4"))
        clip3 = create_dummy_video(str(tmp_path / "clip3.mp4"))
        
        clips = [clip1, clip2, clip3]
        # Magnitudes: 0.1 (Static), 1.0 (Slow), 10.0 (Fast)
        magnitudes = {
            "clip1": 0.1,
            "clip2": 1.0,
            "clip3": 10.0
        }
        
        mask_dir = str(tmp_path / "masks")
        report_path = str(tmp_path / "stratification_report.json")
        
        result = process_dataset_stratification(
            clips, magnitudes, mask_dir, report_path
        )
        
        assert len(result) == 3
        assert os.path.exists(report_path)
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        assert report["total_clips"] == 3
        assert report["distribution"]["Static"] == 1
        assert report["distribution"]["Slow Rigid"] == 1
        assert report["distribution"]["Fast Non-Rigid"] == 1
        assert 0.5 in report["thresholds_used"]
        assert 5.0 in report["thresholds_used"]

    def test_load_processed_clips(self, tmp_path):
        report_path = str(tmp_path / "report.json")
        dummy_data = {"total_clips": 1, "distribution": {}}
        with open(report_path, 'w') as f:
            json.dump(dummy_data, f)
        
        loaded = load_processed_clips(report_path)
        assert loaded == dummy_data
        
        empty = load_processed_clips(str(tmp_path / "nonexistent.json"))
        assert empty == []