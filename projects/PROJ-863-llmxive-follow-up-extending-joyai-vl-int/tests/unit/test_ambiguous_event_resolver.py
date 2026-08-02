"""
Unit tests for src.data_synthesis.ambiguous_event_resolver

Verifies that the deterministic rules for handling ambiguous events
(sitting vs falling) work correctly based on velocity thresholds.

Task: T015 [US1] Implement logic to handle ambiguous events with deterministic rules
"""
import pytest
import math
from src.data_synthesis.models import SyntheticVideoFrame
from src.data_synthesis.ambiguous_event_resolver import (
    AmbiguousEventResolver,
    AmbiguousEventContext,
    ResolvedEvent,
    VELOCITY_THRESHOLD_SITTING_FALLING
)

class TestAmbiguousEventResolver:
    """Tests for the AmbiguousEventResolver class."""
    
    def test_velocity_calculation_zero(self):
        """Test velocity calculation when frames are identical."""
        resolver = AmbiguousEventResolver()
        frame1 = SyntheticVideoFrame(timestamp=1.0, person_bbox=[100, 100, 50, 50], frame_index=0)
        frame2 = SyntheticVideoFrame(timestamp=2.0, person_bbox=[100, 100, 50, 50], frame_index=1)
        
        v = resolver.calculate_velocity(frame1, frame2)
        assert v == 0.0
    
    def test_velocity_calculation_linear(self):
        """Test velocity calculation with known linear movement."""
        resolver = AmbiguousEventResolver()
        # Move 100 pixels in 2 seconds -> 50 px/s
        frame1 = SyntheticVideoFrame(timestamp=1.0, person_bbox=[0, 0, 10, 10], frame_index=0)
        frame2 = SyntheticVideoFrame(timestamp=3.0, person_bbox=[100, 0, 10, 10], frame_index=1)
        
        v = resolver.calculate_velocity(frame1, frame2)
        assert math.isclose(v, 50.0, rel_tol=1e-5)
    
    def test_resolve_fall_high_velocity(self):
        """Test that high velocity results in 'critical' label."""
        resolver = AmbiguousEventResolver(velocity_threshold=100.0)
        
        # Create sequence with velocity > 100
        frames = []
        for i in range(5):
            # Move 30 pixels every 0.1s -> 300 px/s
            frames.append(SyntheticVideoFrame(
                timestamp=i * 0.1,
                person_bbox=[i * 30, 100, 20, 20],
                frame_index=i
            ))
        
        context = AmbiguousEventContext(
            frame_sequence=frames,
            start_index=0,
            end_index=4,
            label="ambiguous",
            confidence=0.5
        )
        
        result = resolver.resolve_sequence(context)
        assert result.resolved_label == "critical"
        assert "Average velocity" in result.resolution_reason
    
    def test_resolve_sit_low_velocity(self):
        """Test that low velocity results in 'silence' label."""
        resolver = AmbiguousEventResolver(velocity_threshold=100.0)
        
        # Create sequence with velocity < 100
        frames = []
        for i in range(5):
            # Move 5 pixels every 0.1s -> 50 px/s
            frames.append(SyntheticVideoFrame(
                timestamp=i * 0.1,
                person_bbox=[i * 5, 100, 20, 20],
                frame_index=i
            ))
        
        context = AmbiguousEventContext(
            frame_sequence=frames,
            start_index=0,
            end_index=4,
            label="ambiguous",
            confidence=0.5
        )
        
        result = resolver.resolve_sequence(context)
        assert result.resolved_label == "silence"
        assert "within sitting thresholds" in result.resolution_reason
    
    def test_resolve_fall_vertical_displacement(self):
        """Test fall detection based on vertical displacement even with moderate velocity."""
        resolver = AmbiguousEventResolver(velocity_threshold=100.0)
        
        frames = []
        # Large vertical drop
        start_y = 100
        end_y = 200
        for i in range(5):
            y = start_y + (i * ((end_y - start_y) / 4))
            frames.append(SyntheticVideoFrame(
                timestamp=i * 0.1,
                person_bbox=[100, y, 20, 20],
                frame_index=i
            ))
        
        context = AmbiguousEventContext(
            frame_sequence=frames,
            start_index=0,
            end_index=4,
            label="ambiguous",
            confidence=0.5
        )
        
        result = resolver.resolve_sequence(context)
        # Should detect fall due to vertical displacement
        assert result.resolved_label == "critical"
    
    def test_empty_sequence(self):
        """Test handling of empty sequence."""
        resolver = AmbiguousEventResolver()
        context = AmbiguousEventContext(
            frame_sequence=[],
            start_index=0,
            end_index=0,
            label="ambiguous",
            confidence=0.5
        )
        
        result = resolver.resolve_sequence(context)
        assert result.resolved_label == "silence"
        assert "Empty sequence" in result.resolution_reason
    
    def test_no_person_bbox(self):
        """Test handling of frames without person bbox."""
        resolver = AmbiguousEventResolver()
        frames = [
            SyntheticVideoFrame(timestamp=1.0, person_bbox=None, frame_index=0),
            SyntheticVideoFrame(timestamp=2.0, person_bbox=None, frame_index=1)
        ]
        
        v = resolver.calculate_velocity(frames[0], frames[1])
        assert v == 0.0

def test_deterministic_rule_application():
    """
    Integration test: Verify that the deterministic rules consistently
    classify the same ambiguous input as the same label.
    """
    resolver = AmbiguousEventResolver(velocity_threshold=150.0)
    
    # Generate a specific "ambiguous" sequence
    frames = []
    for i in range(10):
        # Velocity ~ 160 px/s (just above threshold)
        frames.append(SyntheticVideoFrame(
            timestamp=i * 0.1,
            person_bbox=[i * 16, 100, 20, 20],
            frame_index=i
        ))
    
    context = AmbiguousEventContext(
        frame_sequence=frames,
        start_index=0,
        end_index=9,
        label="ambiguous",
        confidence=0.5
    )
    
    # Run multiple times to ensure determinism
    results = [resolver.resolve_sequence(context) for _ in range(5)]
    
    # All results must be identical
    first_label = results[0].resolved_label
    first_reason = results[0].resolution_reason
    
    for r in results[1:]:
        assert r.resolved_label == first_label
        assert r.resolution_reason == first_reason
    
    assert first_label == "critical"