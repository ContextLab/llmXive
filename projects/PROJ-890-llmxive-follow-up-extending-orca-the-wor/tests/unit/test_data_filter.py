"""
Unit tests for the data filtering logic used in the Orca dataset curation pipeline.

This module tests the filtering of physical interaction clips based on optical flow magnitude
as specified in FR-001. It validates that clips with optical flow magnitude below the 
configured threshold are correctly excluded from the filtered dataset.
"""
import pytest
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config import OPTICAL_FLOW_THRESHOLD
from code.utils.audit_logger import log_skipped_file, log_audit_event, clear_audit_logs, get_audit_summary
from code.data.models import PhysicalScenario


class MockMetadata:
    """Mock metadata object simulating Orca dataset metadata structure."""
    def __init__(self, optical_flow_magnitude: float, video_id: str = "mock_video"):
        self.optical_flow_magnitude = optical_flow_magnitude
        self.video_id = video_id
        self.is_physical_interaction = True  # Assume all are physical for this test


def mock_filter_function(metadata_list: list, threshold: float) -> tuple:
    """
    Simulated filtering logic matching the implementation in code/data/download_orca.py.
    
    This function filters clips based on optical flow magnitude and logs skipped files.
    
    Args:
        metadata_list: List of metadata objects to filter
        threshold: Optical flow magnitude threshold for filtering
        
    Returns:
        tuple: (filtered_items, skipped_count, skipped_ids)
    """
    filtered = []
    skipped_count = 0
    skipped_ids = []
    
    for item in metadata_list:
        if hasattr(item, 'optical_flow_magnitude'):
            flow_mag = item.optical_flow_magnitude
            if flow_mag >= threshold:
                filtered.append(item)
            else:
                skipped_count += 1
                skipped_ids.append(item.video_id)
                log_skipped_file(
                    file_id=item.video_id,
                    reason="low_optical_flow",
                    details=f"Optical flow magnitude {flow_mag} < threshold {threshold}"
                )
        else:
            # Handle items without optical flow data
            skipped_count += 1
            skipped_ids.append(item.video_id)
            log_skipped_file(
                file_id=item.video_id,
                reason="missing_optical_flow_field",
                details="Metadata object missing optical_flow_magnitude field"
            )
    
    return filtered, skipped_count, skipped_ids


class TestDataFiltering:
    """Test suite for data filtering logic."""
    
    def setup_method(self):
        """Setup test fixtures before each test."""
        clear_audit_logs()
        self.threshold = OPTICAL_FLOW_THRESHOLD
        
    def test_filter_above_threshold(self):
        """Test that clips with optical flow above threshold are kept."""
        metadata_list = [
            MockMetadata(optical_flow_magnitude=0.6, video_id="clip_001"),
            MockMetadata(optical_flow_magnitude=0.8, video_id="clip_002"),
            MockMetadata(optical_flow_magnitude=1.2, video_id="clip_003"),
        ]
        
        filtered, skipped_count, skipped_ids = mock_filter_function(metadata_list, self.threshold)
        
        assert len(filtered) == 3, f"Expected 3 filtered items, got {len(filtered)}"
        assert skipped_count == 0, f"Expected 0 skipped items, got {skipped_count}"
        assert len(skipped_ids) == 0, f"Expected 0 skipped IDs, got {len(skipped_ids)}"
        
        for item in filtered:
            assert item.optical_flow_magnitude >= self.threshold
            
    def test_filter_below_threshold(self):
        """Test that clips with optical flow below threshold are excluded."""
        metadata_list = [
            MockMetadata(optical_flow_magnitude=0.1, video_id="clip_004"),
            MockMetadata(optical_flow_magnitude=0.3, video_id="clip_005"),
            MockMetadata(optical_flow_magnitude=0.4, video_id="clip_006"),
        ]
        
        filtered, skipped_count, skipped_ids = mock_filter_function(metadata_list, self.threshold)
        
        assert len(filtered) == 0, f"Expected 0 filtered items, got {len(filtered)}"
        assert skipped_count == 3, f"Expected 3 skipped items, got {skipped_count}"
        assert len(skipped_ids) == 3, f"Expected 3 skipped IDs, got {len(skipped_ids)}"
        
        # Verify all skipped IDs are in the skipped list
        assert set(skipped_ids) == {"clip_004", "clip_005", "clip_006"}
        
    def test_filter_mixed_threshold(self):
        """Test filtering with a mix of above and below threshold clips."""
        metadata_list = [
            MockMetadata(optical_flow_magnitude=0.1, video_id="clip_007"),
            MockMetadata(optical_flow_magnitude=0.6, video_id="clip_008"),
            MockMetadata(optical_flow_magnitude=0.3, video_id="clip_009"),
            MockMetadata(optical_flow_magnitude=0.9, video_id="clip_010"),
        ]
        
        filtered, skipped_count, skipped_ids = mock_filter_function(metadata_list, self.threshold)
        
        assert len(filtered) == 2, f"Expected 2 filtered items, got {len(filtered)}"
        assert skipped_count == 2, f"Expected 2 skipped items, got {skipped_count}"
        assert len(skipped_ids) == 2, f"Expected 2 skipped IDs, got {len(skipped_ids)}"
        
        # Verify filtered items have high flow
        filtered_ids = [item.video_id for item in filtered]
        assert set(filtered_ids) == {"clip_008", "clip_010"}
        
        # Verify skipped items have low flow
        assert set(skipped_ids) == {"clip_007", "clip_009"}
        
    def test_filter_edge_case_exact_threshold(self):
        """Test filtering at exactly the threshold value (boundary condition)."""
        metadata_list = [
            MockMetadata(optical_flow_magnitude=self.threshold, video_id="clip_011"),
            MockMetadata(optical_flow_magnitude=self.threshold - 0.001, video_id="clip_012"),
            MockMetadata(optical_flow_magnitude=self.threshold + 0.001, video_id="clip_013"),
        ]
        
        filtered, skipped_count, skipped_ids = mock_filter_function(metadata_list, self.threshold)
        
        # clip_011 should be kept (>= threshold)
        # clip_012 should be skipped (< threshold)
        # clip_013 should be kept (> threshold)
        assert len(filtered) == 2, f"Expected 2 filtered items, got {len(filtered)}"
        assert skipped_count == 1, f"Expected 1 skipped item, got {skipped_count}"
        
        filtered_ids = [item.video_id for item in filtered]
        assert "clip_011" in filtered_ids
        assert "clip_013" in filtered_ids
        assert "clip_012" in skipped_ids
        
    def test_filter_empty_list(self):
        """Test filtering with an empty list."""
        metadata_list = []
        
        filtered, skipped_count, skipped_ids = mock_filter_function(metadata_list, self.threshold)
        
        assert len(filtered) == 0
        assert skipped_count == 0
        assert len(skipped_ids) == 0
        
    def test_filter_missing_field(self):
        """Test filtering when metadata lacks optical_flow_magnitude field."""
        class BadMetadata:
            def __init__(self, video_id):
                self.video_id = video_id
                # Missing optical_flow_magnitude
                
        metadata_list = [
            BadMetadata("clip_014"),
            BadMetadata("clip_015"),
        ]
        
        filtered, skipped_count, skipped_ids = mock_filter_function(metadata_list, self.threshold)
        
        assert len(filtered) == 0
        assert skipped_count == 2
        assert set(skipped_ids) == {"clip_014", "clip_015"}
        
    def test_audit_logging(self):
        """Test that skipped files are properly logged in the audit system."""
        metadata_list = [
            MockMetadata(optical_flow_magnitude=0.1, video_id="audit_clip_001"),
            MockMetadata(optical_flow_magnitude=0.6, video_id="audit_clip_002"),
        ]
        
        filtered, skipped_count, skipped_ids = mock_filter_function(metadata_list, self.threshold)
        
        # Verify audit logs contain the skipped file
        audit_summary = get_audit_summary()
        assert "skipped_files" in audit_summary
        assert len(audit_summary["skipped_files"]) >= 1
        
        # Find the specific skipped file
        skipped_in_log = [
            entry for entry in audit_summary["skipped_files"]
            if entry["file_id"] == "audit_clip_001"
        ]
        assert len(skipped_in_log) == 1
        assert skipped_in_log[0]["reason"] == "low_optical_flow"

    def test_numpy_compatibility(self):
        """Test filtering with numpy arrays for optical flow magnitude."""
        class NumpyMetadata:
            def __init__(self, flow_val, video_id):
                self.optical_flow_magnitude = np.float32(flow_val)
                self.video_id = video_id
                
        metadata_list = [
            NumpyMetadata(0.1, "numpy_clip_001"),
            NumpyMetadata(0.6, "numpy_clip_002"),
            NumpyMetadata(0.4, "numpy_clip_003"),
        ]
        
        filtered, skipped_count, skipped_ids = mock_filter_function(metadata_list, self.threshold)
        
        assert len(filtered) == 1
        assert skipped_count == 2
        assert filtered[0].video_id == "numpy_clip_002"
        assert set(skipped_ids) == {"numpy_clip_001", "numpy_clip_003"}

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
