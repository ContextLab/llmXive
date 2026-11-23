import pytest
import sys
import os
from pathlib import Path
from typing import List, Dict, Any
from src.agents.evomem_conflict import EvoMemConflict
from unittest.mock import patch, MagicMock

class MockConflictDetector:
    """Mock detector for testing fallback logic without loading real models."""
    
    def __init__(self, return_conflicts: bool = False, return_error: bool = False):
        self.return_conflicts = return_conflicts
        self.return_error = return_error
        self.threshold = 0.90

    def detect_conflicts(self, texts: List[str]):
        if self.return_error:
            raise RuntimeError("Simulated detector failure")
        
        results = []
        for i, text in enumerate(texts):
            # Create a mock result object with a score attribute
            mock_result = MagicMock()
            if self.return_conflicts:
                # Make every other text a conflict for testing
                mock_result.score = 0.95 if i % 2 == 0 else 0.5
            else:
                mock_result.score = 0.5
            results.append(mock_result)
        return results

@pytest.fixture
def mock_patches():
    """Generate a list of mock patches."""
    return [
        {"id": 1, "state": "Patch A", "timestamp": "t1"},
        {"id": 2, "state": "Patch B", "timestamp": "t2"},
        {"id": 3, "state": "Patch C", "timestamp": "t3"},
        {"id": 4, "state": "Patch D", "timestamp": "t4"},
        {"id": 5, "state": "Latest State", "timestamp": "t5"} # Last one is latest
    ]

class TestEvoMemConflictFallback:
    """Tests for FR-002 and FR-007 fallback logic in EvoMemConflict."""

    @patch('src.agents.evomem_conflict.ConflictDetector')
    def test_fallback_no_conflicts(self, MockDetectorClass, mock_patches):
        """
        Test that if no conflicts are detected, the agent retrieves:
        Latest State + 2 most recent non-conflict patches.
        """
        # Setup mock to return NO conflicts
        mock_detector_instance = MagicMock()
        mock_detector_instance.detect_conflicts.return_value = [
            MagicMock(score=0.1), MagicMock(score=0.2), MagicMock(score=0.3), 
            MagicMock(score=0.4), MagicMock(score=0.5) # All below threshold
        ]
        MockDetectorClass.return_value = mock_detector_instance

        agent = EvoMemConflict(threshold=0.90)
        
        # Execute retrieval
        result = agent.retrieve_patches(mock_patches)
        
        # Assertions
        # 1. Latest state must be present
        assert len(result) > 0
        assert result[0]["id"] == 5 # Latest State
        
        # 2. Should have exactly 3 items: Latest + 2 most recent non-conflicts
        #    Non-conflicts are IDs 1, 2, 3, 4. Most recent are 4 and 3.
        assert len(result) == 3, f"Expected 3 patches (1 latest + 2 recent), got {len(result)}: {result}"
        
        # 3. Check IDs: Latest (5) + 4 + 3
        ids = [p["id"] for p in result]
        assert 5 in ids
        assert 4 in ids
        assert 3 in ids
        assert 1 not in ids and 2 not in ids # Older ones should be excluded

    @patch('src.agents.evomem_conflict.ConflictDetector')
    def test_fallback_detector_failure(self, MockDetectorClass, mock_patches):
        """
        Test that if the detector fails (exception), the agent falls back to:
        Latest State + 2 most recent non-conflict patches.
        """
        # Setup mock to raise an error
        mock_detector_instance = MagicMock()
        mock_detector_instance.detect_conflicts.side_effect = RuntimeError("Timeout")
        MockDetectorClass.return_value = mock_detector_instance

        agent = EvoMemConflict(threshold=0.90)
        
        # Execute retrieval
        result = agent.retrieve_patches(mock_patches)
        
        # Assertions
        # Should fall back to same logic as "no conflicts"
        assert len(result) == 3, f"Expected 3 patches on failure, got {len(result)}"
        assert result[0]["id"] == 5 # Latest
        
        # Most recent non-conflicts (since all are treated as non-conflict on failure)
        ids = [p["id"] for p in result]
        assert 5 in ids
        assert 4 in ids
        assert 3 in ids

    @patch('src.agents.evomem_conflict.ConflictDetector')
    def test_no_fallback_when_conflicts_found(self, MockDetectorClass, mock_patches):
        """
        Test that if conflicts ARE found, the fallback logic is NOT triggered.
        Instead, it returns Latest + Conflicts.
        """
        # Setup mock to return conflicts
        mock_detector_instance = MagicMock()
        # Make ID 2 and 4 conflicts (indices 1 and 3)
        mock_detector_instance.detect_conflicts.return_value = [
            MagicMock(score=0.1), # ID 1: No
            MagicMock(score=0.95), # ID 2: Yes
            MagicMock(score=0.2), # ID 3: No
            MagicMock(score=0.95), # ID 4: Yes
            MagicMock(score=0.3)  # ID 5: No
        ]
        MockDetectorClass.return_value = mock_detector_instance

        agent = EvoMemConflict(threshold=0.90)
        
        result = agent.retrieve_patches(mock_patches)
        
        # Assertions
        # Should contain Latest (5) + Conflicts (2, 4)
        # Total 3 items
        assert len(result) == 3
        
        ids = [p["id"] for p in result]
        assert 5 in ids
        assert 2 in ids
        assert 4 in ids
        assert 1 not in ids and 3 not in ids

    @patch('src.agents.evomem_conflict.ConflictDetector')
    def test_fallback_with_fewer_than_2_non_conflicts(self, MockDetectorClass):
        """
        Test edge case: If there are fewer than 2 non-conflict patches available,
        return whatever is available (Latest + available non-conflicts).
        """
        # Only 2 patches total: Latest and one other
        few_patches = [
            {"id": 1, "state": "Old", "timestamp": "t1"},
            {"id": 2, "state": "Latest", "timestamp": "t2"}
        ]
        
        mock_detector_instance = MagicMock()
        mock_detector_instance.detect_conflicts.return_value = [
            MagicMock(score=0.1), MagicMock(score=0.1) # No conflicts
        ]
        MockDetectorClass.return_value = mock_detector_instance

        agent = EvoMemConflict(threshold=0.90)
        result = agent.retrieve_patches(few_patches)
        
        # Should return Latest + 1 non-conflict (since only 1 exists)
        assert len(result) == 2
        ids = [p["id"] for p in result]
        assert 2 in ids
        assert 1 in ids

    @patch('src.agents.evomem_conflict.ConflictDetector')
    def test_fallback_with_empty_patches(self, MockDetectorClass):
        """
        Test behavior when input patches list is empty.
        """
        mock_detector_instance = MagicMock()
        MockDetectorClass.return_value = mock_detector_instance

        agent = EvoMemConflict(threshold=0.90)
        result = agent.retrieve_patches([])
        
        assert result == []