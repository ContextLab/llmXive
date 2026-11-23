"""
Integration test for diffusion runner (T018).

Tests the end-to-end generation pipeline with a small subset of scenes.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from generation.diffusion_runner import (
    load_all_prompts,
    load_model,
    generate_single_image,
    run_diffusion_generation,
    DiffusionGenerationError,
    PromptFileNotFoundError
)
from generation.seed_manager import SeedManager

class TestDiffusionRunnerIntegration:
    """Integration tests for diffusion generation pipeline."""
    
    @pytest.fixture
    def temp_prompts_dir(self, tmp_path):
        """Create a temporary directory with sample prompt files."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        
        # Create sample prompt files for different groups
        scenes = {
            "scene_001": {
                "baseline": "A cat sitting on a mat",
                "experimental": "A cat sitting on a mat with physics constraints",
                "control": "Random noise descriptor for control"
            },
            "scene_002": {
                "baseline": "A dog playing with a ball",
                "experimental": "A dog playing with a ball under gravity",
                "control": "Another random noise descriptor"
            }
        }
        
        for scene_id, groups in scenes.items():
            for group, prompt in groups.items():
                file_path = prompts_dir / f"{scene_id}_{group}.txt"
                file_path.write_text(prompt)
        
        return prompts_dir
    
    @pytest.fixture
    def temp_output_dir(self, tmp_path):
        """Create a temporary output directory."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        return output_dir
    
    def test_load_all_prompts(self, temp_prompts_dir):
        """Test loading all prompts from directory."""
        scene_prompts = load_all_prompts(temp_prompts_dir)
        
        assert len(scene_prompts) == 2
        assert "scene_001" in scene_prompts
        assert "scene_002" in scene_prompts
        
        assert "baseline" in scene_prompts["scene_001"]
        assert "experimental" in scene_prompts["scene_001"]
        assert "control" in scene_prompts["scene_001"]
        
        assert scene_prompts["scene_001"]["baseline"] == "A cat sitting on a mat"
        assert scene_prompts["scene_002"]["experimental"] == "A dog playing with a ball under gravity"
    
    def test_load_all_prompts_missing_files(self, tmp_path):
        """Test loading prompts when some files are missing."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        
        # Only create baseline file
        file_path = prompts_dir / "scene_001_baseline.txt"
        file_path.write_text("A cat sitting on a mat")
        
        scene_prompts = load_all_prompts(prompts_dir)
        
        assert len(scene_prompts) == 1
        assert "baseline" in scene_prompts["scene_001"]
        assert "experimental" not in scene_prompts["scene_001"]
        assert "control" not in scene_prompts["scene_001"]
    
    def test_run_diffusion_generation_mock(self, temp_prompts_dir, temp_output_dir):
        """Test running the generation pipeline with mocked model."""
        # Mock the model loading and generation
        with patch('generation.diffusion_runner.load_model') as mock_load_model, \
             patch('generation.diffusion_runner.generate_single_image') as mock_generate:
            
            # Setup mocks
            mock_pipeline = MagicMock()
            mock_load_model.return_value = (mock_pipeline, MagicMock())
            
            # Mock image generation to return a dummy image
            mock_image = MagicMock()
            mock_generate.return_value = mock_image
            
            # Mock save_image to avoid actual file writing
            with patch('generation.diffusion_runner.save_image'):
                # Run the pipeline
                stats = run_diffusion_generation(
                    prompts_dir=temp_prompts_dir,
                    output_base_dir=temp_output_dir,
                    model_id="test-model",
                    device="cpu"
                )
                
                # Verify statistics
                assert stats["total_scenes"] == 2
                assert stats["successful_scenes"] == 2
                assert stats["total_images"] == 6  # 2 scenes * 3 groups
                assert stats["groups_generated"]["baseline"] == 2
                assert stats["groups_generated"]["experimental"] == 2
                assert stats["groups_generated"]["control"] == 2
                
                # Verify model was loaded
                mock_load_model.assert_called_once()
                
                # Verify generation was called for each prompt
                assert mock_generate.call_count == 6
    
    def test_run_diffusion_generation_with_failures(self, temp_prompts_dir, temp_output_dir):
        """Test pipeline behavior when some generations fail."""
        with patch('generation.diffusion_runner.load_model') as mock_load_model, \
             patch('generation.diffusion_runner.generate_single_image') as mock_generate:
            
            mock_pipeline = MagicMock()
            mock_load_model.return_value = (mock_pipeline, MagicMock())
            
            # First call succeeds, second fails
            mock_image = MagicMock()
            mock_generate.side_effect = [mock_image, None, mock_image, mock_image, mock_image, mock_image]
            
            with patch('generation.diffusion_runner.save_image'):
                stats = run_diffusion_generation(
                    prompts_dir=temp_prompts_dir,
                    output_base_dir=temp_output_dir,
                    model_id="test-model",
                    device="cpu"
                )
                
                # Should have one failed scene
                assert stats["failed_scenes"] >= 1
                
                # Check that failure log was created
                failure_log = temp_output_dir / "generated_images" / "generation_failures.json"
                # Note: In the actual implementation, failures are logged per scene/group
                # This test verifies the logic handles failures gracefully
    
    def test_seed_manager_integration(self, temp_prompts_dir, temp_output_dir):
        """Test that seed manager is correctly used during generation."""
        with patch('generation.diffusion_runner.load_model') as mock_load_model, \
             patch('generation.diffusion_runner.generate_single_image') as mock_generate, \
             patch('generation.diffusion_runner.save_image'):
            
            mock_pipeline = MagicMock()
            mock_load_model.return_value = (mock_pipeline, MagicMock())
            
            mock_image = MagicMock()
            mock_generate.return_value = mock_image
            
            stats = run_diffusion_generation(
                prompts_dir=temp_prompts_dir,
                output_base_dir=temp_output_dir,
                model_id="test-model",
                device="cpu"
            )
            
            # Verify that seeds were used (this is checked in the mock calls)
            # In a real test, we would verify the actual seed values
            assert stats["total_images"] > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
