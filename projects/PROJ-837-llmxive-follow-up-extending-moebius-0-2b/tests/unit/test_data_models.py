import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from models.data_models import MaskedRegion, InferenceResult, GatingState

class TestMaskedRegion:
    def test_create_masked_region(self):
        region = MaskedRegion(
            image_id="test_001",
            mask_area=0.25,
            gradient_variance=0.15,
            texture_entropy=0.8
        )
        
        assert region.image_id == "test_001"
        assert region.mask_area == 0.25
        assert region.gradient_variance == 0.15
        assert region.texture_entropy == 0.8

    def test_masked_region_defaults(self):
        region = MaskedRegion(image_id="test_002")
        
        assert region.image_id == "test_002"
        assert region.mask_area == 0.0
        assert region.gradient_variance == 0.0
        assert region.texture_entropy == 0.0

class TestInferenceResult:
    def test_create_inference_result(self):
        result = InferenceResult(
            image_id="test_003",
            latency_ms=150.5,
            psnr=28.5,
            ssim=0.85,
            rank_used=3
        )
        
        assert result.image_id == "test_003"
        assert result.latency_ms == 150.5
        assert result.psnr == 28.5
        assert result.ssim == 0.85
        assert result.rank_used == 3

    def test_inference_result_serialization(self):
        result = InferenceResult(
            image_id="test_004",
            latency_ms=200.0,
            psnr=30.0,
            ssim=0.9,
            rank_used=2
        )
        
        data = result.to_dict()
        assert data['image_id'] == "test_004"
        assert data['latency_ms'] == 200.0
        assert data['psnr'] == 30.0

class TestGatingState:
    def test_create_gating_state(self):
        state = GatingState(
            complexity_score=3.5,
            predicted_rank=3,
            confidence=0.92
        )
        
        assert state.complexity_score == 3.5
        assert state.predicted_rank == 3
        assert state.confidence == 0.92

    def test_gating_state_rank_clamping(self):
        state = GatingState(
            complexity_score=0.5,
            predicted_rank=1,
            confidence=0.95
        )
        
        assert state.predicted_rank >= 1
        assert state.predicted_rank <= 5

    def test_gating_state_high_confidence(self):
        state = GatingState(
            complexity_score=4.8,
            predicted_rank=5,
            confidence=0.99
        )
        
        assert state.confidence > 0.9
        assert state.predicted_rank == 5
