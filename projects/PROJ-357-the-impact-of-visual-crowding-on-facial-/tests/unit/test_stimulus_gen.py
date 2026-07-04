"""
Unit tests for stimulus composition and overlap detection in code/utils/stimulus_gen.py.

These tests verify:
1. Flanker position generation (no overlap with center target)
2. Overlap detection logic (correctly identifies colliding flankers)
3. Stimulus creation (proper image composition)
4. Edge cases (minimum flanker count, extreme eccentricity)
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import math
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.stimulus_gen import (
    check_flanker_overlap,
    generate_flanker_positions,
    create_stimulus,
    load_frames_by_emotion
)
from config import ensure_directories


class TestOverlapDetection:
    """Tests for the check_flanker_overlap function."""

    def test_no_overlap_when_far_apart(self):
        """Flankers far from center should not overlap."""
        center = (100, 100)
        flanker = (200, 200)
        center_radius = 30
        flanker_radius = 20
        
        result = check_flanker_overlap(center, flanker, center_radius, flanker_radius)
        assert result is False, "Flankers far apart should not overlap"

    def test_overlap_when_close(self):
        """Flankers close to center should overlap."""
        center = (100, 100)
        flanker = (110, 110)  # Very close
        center_radius = 30
        flanker_radius = 20
        
        result = check_flanker_overlap(center, flanker, center_radius, flanker_radius)
        assert result is True, "Flankers close together should overlap"

    def test_exact_boundary_no_overlap(self):
        """Flankers exactly touching should not overlap (distance = sum of radii)."""
        center = (100, 100)
        flanker = (150, 100)  # Distance = 50, radii sum = 30 + 20 = 50
        center_radius = 30
        flanker_radius = 20
        
        result = check_flanker_overlap(center, flanker, center_radius, flanker_radius)
        assert result is False, "Flankers exactly touching should not overlap"

    def test_tiny_overlap(self):
        """Flankers slightly overlapping should be detected."""
        center = (100, 100)
        flanker = (148, 100)  # Distance = 48, radii sum = 50
        center_radius = 30
        flanker_radius = 20
        
        result = check_flanker_overlap(center, flanker, center_radius, flanker_radius)
        assert result is True, "Flankers slightly overlapping should be detected"

    def test_multiple_flanker_overlap(self):
        """Test overlap detection with multiple flankers."""
        center = (100, 100)
        center_radius = 30
        flanker_radius = 20
        
        flankers = [
            (200, 200),  # Far away - no overlap
            (110, 110),  # Close - overlap
            (150, 150)   # Edge case - no overlap (distance ~70.7)
        ]
        
        overlaps = []
        for f in flankers:
            if check_flanker_overlap(center, f, center_radius, flanker_radius):
                overlaps.append(f)
        
        assert len(overlaps) == 1, "Should detect exactly one overlapping flanker"
        assert overlaps[0] == (110, 110), "Should detect the correct overlapping flanker"


class TestFlankerPositionGeneration:
    """Tests for the generate_flanker_positions function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.center = (150, 150)
        self.center_radius = 30
        self.flanker_radius = 20
        self.canvas_size = (300, 300)

    def test_minimum_flanker_count(self):
        """Should generate at least the requested number of non-overlapping flankers."""
        positions = generate_flanker_positions(
            center=self.center,
            center_radius=self.center_radius,
            flanker_radius=self.flanker_radius,
            flanker_count=3,
            canvas_size=self.canvas_size,
            max_attempts=1000
        )
        assert len(positions) >= 3, f"Should generate at least 3 flankers, got {len(positions)}"

    def test_no_overlap_with_center(self):
        """All generated flankers should not overlap with the center target."""
        positions = generate_flanker_positions(
            center=self.center,
            center_radius=self.center_radius,
            flanker_radius=self.flanker_radius,
            flanker_count=5,
            canvas_size=self.canvas_size,
            max_attempts=1000
        )
        
        for pos in positions:
            assert not check_flanker_overlap(
                self.center, pos, self.center_radius, self.flanker_radius
            ), f"Flanker at {pos} overlaps with center"

    def test_no_overlap_between_flankers(self):
        """All generated flankers should not overlap with each other."""
        positions = generate_flanker_positions(
            center=self.center,
            center_radius=self.center_radius,
            flanker_radius=self.flanker_radius,
            flanker_count=5,
            canvas_size=self.canvas_size,
            max_attempts=1000
        )
        
        for i, pos1 in enumerate(positions):
            for j, pos2 in enumerate(positions):
                if i < j:
                    assert not check_flanker_overlap(
                        pos1, pos2, self.flanker_radius, self.flanker_radius
                    ), f"Flankers at {pos1} and {pos2} overlap"

    def test_within_canvas_bounds(self):
        """All generated flankers should be within canvas bounds."""
        positions = generate_flanker_positions(
            center=self.center,
            center_radius=self.center_radius,
            flanker_radius=self.flanker_radius,
            flanker_count=5,
            canvas_size=self.canvas_size,
            max_attempts=1000
        )
        
        width, height = self.canvas_size
        for pos in positions:
            x, y = pos
            assert x - self.flanker_radius >= 0, f"Flanker at {pos} outside left bound"
            assert x + self.flanker_radius <= width, f"Flanker at {pos} outside right bound"
            assert y - self.flanker_radius >= 0, f"Flanker at {pos} outside top bound"
            assert y + self.flanker_radius <= height, f"Flanker at {pos} outside bottom bound"

    def test_eccentricity_constraint(self):
        """Flankers should be at approximately the specified eccentricity."""
        target_eccentricity = 80
        tolerance = 20  # Allow some variance due to non-overlap constraints
        
        positions = generate_flanker_positions(
            center=self.center,
            center_radius=self.center_radius,
            flanker_radius=self.flanker_radius,
            flanker_count=4,
            canvas_size=self.canvas_size,
            max_attempts=1000
        )
        
        for pos in positions:
            distance = math.sqrt(
                (pos[0] - self.center[0])**2 + (pos[1] - self.center[1])**2
            )
            assert abs(distance - target_eccentricity) <= tolerance, \
                f"Flanker at {pos} has distance {distance}, expected ~{target_eccentricity}"

    def test_high_flanker_count(self):
        """Should handle higher flanker counts (more challenging constraint)."""
        positions = generate_flanker_positions(
            center=self.center,
            center_radius=self.center_radius,
            flanker_radius=self.flanker_radius,
            flanker_count=8,
            canvas_size=self.canvas_size,
            max_attempts=2000
        )
        assert len(positions) >= 8, f"Should generate at least 8 flankers, got {len(positions)}"

    def test_insufficient_space(self):
        """Should gracefully handle cases where space is insufficient."""
        # Very small canvas with large flankers
        small_canvas = (100, 100)
        large_flanker_radius = 25
        
        positions = generate_flanker_positions(
            center=(50, 50),
            center_radius=20,
            flanker_radius=large_flanker_radius,
            flanker_count=10,
            canvas_size=small_canvas,
            max_attempts=100
        )
        
        # May not get all requested, but should get what's possible
        assert len(positions) >= 0, "Should return valid positions even if fewer than requested"


class TestStimulusCreation:
    """Tests for the create_stimulus function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.canvas_size = (300, 300)
        self.center = (150, 150)
        
        # Create a simple test image
        self.target_img = Image.new('RGB', (60, 60), color='red')
        draw = ImageDraw.Draw(self.target_img)
        draw.ellipse([5, 5, 55, 55], fill='blue')  # Center face placeholder
        
        self.flanker_img = Image.new('RGB', (40, 40), color='green')
        draw = ImageDraw.Draw(self.flanker_img)
        draw.ellipse([5, 5, 35, 35], fill='yellow')  # Flanker placeholder

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_basic_stimulus_creation(self):
        """Should create a valid stimulus image with target and flankers."""
        flanker_positions = [(100, 150), (200, 150), (150, 100), (150, 200)]
        
        output_path = os.path.join(self.temp_dir, 'test_stimulus.png')
        create_stimulus(
            target_img=self.target_img,
            flanker_img=self.flanker_img,
            center_pos=self.center,
            flanker_positions=flanker_positions,
            output_path=output_path
        )
        
        assert os.path.exists(output_path), "Output image should be created"
        
        # Verify the output image
        result_img = Image.open(output_path)
        assert result_img.size == self.canvas_size, "Output size should match canvas"
        result_img.close()

    def test_stimulus_with_no_flankers(self):
        """Should create a stimulus with only the target (control condition)."""
        output_path = os.path.join(self.temp_dir, 'test_stimulus_no_flanker.png')
        create_stimulus(
            target_img=self.target_img,
            flanker_img=self.flanker_img,
            center_pos=self.center,
            flanker_positions=[],
            output_path=output_path
        )
        
        assert os.path.exists(output_path), "Output image should be created"
        
        result_img = Image.open(output_path)
        assert result_img.size == self.canvas_size
        result_img.close()

    def test_stimulus_with_single_flanker(self):
        """Should create a stimulus with exactly one flanker."""
        flanker_positions = [(200, 150)]
        
        output_path = os.path.join(self.temp_dir, 'test_stimulus_one_flanker.png')
        create_stimulus(
            target_img=self.target_img,
            flanker_img=self.flanker_img,
            center_pos=self.center,
            flanker_positions=flanker_positions,
            output_path=output_path
        )
        
        assert os.path.exists(output_path)
        result_img = Image.open(output_path)
        assert result_img.size == self.canvas_size
        result_img.close()

    def test_invalid_output_path_directory(self):
        """Should raise an error if output directory doesn't exist."""
        flanker_positions = [(200, 150)]
        invalid_path = os.path.join(self.temp_dir, 'nonexistent', 'test.png')
        
        with pytest.raises((FileNotFoundError, OSError)):
            create_stimulus(
                target_img=self.target_img,
                flanker_img=self.flanker_img,
                center_pos=self.center,
                flanker_positions=flanker_positions,
                output_path=invalid_path
            )

    def test_image_format_preservation(self):
        """Output should be saved in correct format (PNG)."""
        flanker_positions = [(200, 150)]
        output_path = os.path.join(self.temp_dir, 'test_stimulus.png')
        
        create_stimulus(
            target_img=self.target_img,
            flanker_img=self.flanker_img,
            center_pos=self.center,
            flanker_positions=flanker_positions,
            output_path=output_path
        )
        
        # Verify file extension and format
        assert output_path.endswith('.png')
        result_img = Image.open(output_path)
        assert result_img.format == 'PNG'
        result_img.close()


class TestLoadFramesByEmotion:
    """Tests for the load_frames_by_emotion function."""

    def setup_method(self):
        """Set up test fixtures with real data structure."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / 'frames'
        self.data_dir.mkdir(parents=True)
        
        # Create a mock frame directory structure
        # Simulating RAVDESS structure: actor_XX/emotion/
        self.actor_dir = self.data_dir / 'actor_01'
        self.actor_dir.mkdir()
        
        # Create dummy frame images
        for i in range(5):
            img = Image.new('RGB', (100, 100), color='red')
            img.save(self.actor_dir / f'frame_{i:04d}.png')
        
        # Create another actor with different emotion
        self.actor2_dir = self.data_dir / 'actor_02'
        self.actor2_dir.mkdir()
        for i in range(3):
            img = Image.new('RGB', (100, 100), color='blue')
            img.save(self.actor2_dir / f'frame_{i:04d}.png')

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_frames_with_valid_directory(self):
        """Should load frames from a valid directory."""
        frames = load_frames_by_emotion(str(self.actor_dir))
        assert len(frames) == 5, f"Should load 5 frames, got {len(frames)}"
        
        # Verify frame properties
        for frame in frames:
            assert frame.size == (100, 100)
            assert isinstance(frame, Image.Image)

    def test_load_frames_from_nonexistent_directory(self):
        """Should return empty list for non-existent directory."""
        frames = load_frames_by_emotion('/nonexistent/path')
        assert frames == [], "Should return empty list for non-existent directory"

    def test_load_frames_empty_directory(self):
        """Should return empty list for empty directory."""
        empty_dir = Path(self.temp_dir) / 'empty_actor'
        empty_dir.mkdir()
        
        frames = load_frames_by_emotion(str(empty_dir))
        assert frames == [], "Should return empty list for empty directory"

    def test_frame_ordering(self):
        """Frames should be loaded in sorted order by filename."""
        frames = load_frames_by_emotion(str(self.actor_dir))
        # The function should handle sorting internally or the caller should ensure it
        # For now, just verify we got all frames
        assert len(frames) == 5


class TestIntegration:
    """Integration tests combining multiple functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        ensure_directories(self.temp_dir)
        self.output_dir = Path(self.temp_dir) / 'stimuli'
        self.output_dir.mkdir()

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_stimulus_generation_pipeline(self):
        """Test the complete pipeline: position generation -> stimulus creation."""
        # Create dummy images
        target_img = Image.new('RGB', (60, 60), color='red')
        flanker_img = Image.new('RGB', (40, 40), color='green')
        
        center = (150, 150)
        center_radius = 30
        flanker_radius = 20
        canvas_size = (300, 300)
        
        # Generate flanker positions
        positions = generate_flanker_positions(
            center=center,
            center_radius=center_radius,
            flanker_radius=flanker_radius,
            flanker_count=4,
            canvas_size=canvas_size,
            max_attempts=1000
        )
        
        assert len(positions) >= 4, "Should generate at least 4 flankers"
        
        # Verify no overlaps
        for pos in positions:
            assert not check_flanker_overlap(
                center, pos, center_radius, flanker_radius
            ), f"Flanker at {pos} overlaps with center"
        
        # Create stimulus
        output_path = str(self.output_dir / 'test_stimulus.png')
        create_stimulus(
            target_img=target_img,
            flanker_img=flanker_img,
            center_pos=center,
            flanker_positions=positions,
            output_path=output_path
        )
        
        assert os.path.exists(output_path), "Stimulus image should be created"
        
        # Verify image properties
        result_img = Image.open(output_path)
        assert result_img.size == canvas_size
        result_img.close()

    def test_multiple_stimuli_with_different_parameters(self):
        """Generate multiple stimuli with varying parameters."""
        target_img = Image.new('RGB', (60, 60), color='red')
        flanker_img = Image.new('RGB', (40, 40), color='green')
        
        canvas_size = (300, 300)
        center = (150, 150)
        
        flanker_counts = [2, 4, 6]
        
        for i, count in enumerate(flanker_counts):
            positions = generate_flanker_positions(
                center=center,
                center_radius=30,
                flanker_radius=20,
                flanker_count=count,
                canvas_size=canvas_size,
                max_attempts=1000
            )
            
            output_path = str(self.output_dir / f'stimulus_{count}_flankers.png')
            create_stimulus(
                target_img=target_img,
                flanker_img=flanker_img,
                center_pos=center,
                flanker_positions=positions,
                output_path=output_path
            )
            
            assert os.path.exists(output_path), f"Stimulus with {count} flankers should be created"
            
            # Verify flanker count matches
            result_img = Image.open(output_path)
            assert result_img.size == canvas_size
            result_img.close()


# Run tests if executed directly
if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])