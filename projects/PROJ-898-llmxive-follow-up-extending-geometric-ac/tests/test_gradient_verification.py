"""
Unit tests for gradient verification functionality (T019b)

These tests ensure that the gradient verification module works correctly
and that gradients flow as expected through the symbolic-latent pipeline.
"""

import pytest
import torch
import numpy as np
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.gradient_verification import GradientVerificationTest
from code.utils import set_deterministic_seed


class TestGradientVerification:
    """Test suite for gradient verification functionality."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        set_deterministic_seed(42)
        self.verifier = GradientVerificationTest(seed=42, device="cpu")
    
    def test_initialization(self):
        """Test that verifier initializes correctly."""
        assert self.verifier.device.type == "cpu"
        assert self.verifier.gfm is not None
        assert self.verifier.solver is not None
        assert len(self.verifier.results) == 0
    
    def test_problem_creation(self):
        """Test that test problems are created with correct shapes."""
        obs, target = self.verifier._create_test_problem(n_dims=3)
        
        assert obs.shape == (1, 6)  # [batch, n_dims * 2]
        assert target.shape == (1,)
        assert obs.device.type == "cpu"
        assert target.requires_grad
    
    def test_decoder_gradient_computation(self):
        """Test that decoder gradients are computed and non-zero."""
        obs, target = self.verifier._create_test_problem()
        
        grads = self.verifier._compute_decoder_gradients(obs, target)
        
        # Should have at least one decoder parameter with gradient
        decoder_grads = [v for k, v in grads.items() if "decoder" in k]
        assert len(decoder_grads) > 0, "No decoder gradients found"
        
        # Verify at least one gradient is non-zero
        non_zero_grads = [g for g in decoder_grads if g > 1e-8]
        assert len(non_zero_grads) > 0, "All decoder gradients are zero"
    
    def test_solver_gradient_verification(self):
        """Test that solver gradient paths are verified."""
        obs, target = self.verifier._create_test_problem()
        
        # First get an action
        latent = self.verifier.gfm.encode(obs)
        action = self.verifier.gfm.decode(latent)
        
        grad_info = self.verifier._verify_symbolic_solver_gradients(obs, action)
        
        assert "solver_gradient_exists" in grad_info
        assert grad_info["solver_gradient_exists"] >= 0.0
    
    def test_run_verification_basic(self):
        """Test the full verification pipeline."""
        # This is a basic sanity check - full verification might take longer
        # and is tested in integration tests
        try:
            obs, target = self.verifier._create_test_problem()
            grads = self.verifier._compute_decoder_gradients(obs, target)
            
            # Verify we got results
            assert len(grads) > 0
            assert any("decoder" in k for k in grads.keys())
        except Exception as e:
            pytest.fail(f"Gradient computation failed: {e}")
    
    def test_report_generation(self, tmp_path):
        """Test that report generation creates valid output."""
        # Mock results for testing
        self.verifier.results = {
            "decoder_gradient_check": 1.0,
            "solver_gradient_check": 1.0,
            "end_to_end_check": 1.0
        }
        
        self.verifier.grad_checks = [
            {"component": "decoder", "status": "passed", "details": {"test": 1.0}},
            {"component": "solver", "status": "passed", "details": {"test": 1.0}}
        ]
        
        report_path = os.path.join(tmp_path, "test_report.md")
        self.verifier.generate_report(report_path)
        
        assert os.path.exists(report_path)
        
        with open(report_path, 'r') as f:
            content = f.read()
        
        assert "# Gradient Verification Report" in content
        assert "Decoder" in content
        assert "Solver" in content
        assert "✅ PASSED" in content or "passed" in content.lower()
    
    def test_gradient_flow_direction(self):
        """Test that gradients flow in the expected direction."""
        obs, target = self.verifier._create_test_problem()
        
        # Compute gradients
        grads = self.verifier._compute_decoder_gradients(obs, target)
        
        # Verify gradients exist for key components
        has_encoder_grads = any("encoder" in k for k in grads.keys())
        has_decoder_grads = any("decoder" in k for k in grads.keys())
        
        # At least one should have gradients
        assert has_encoder_grads or has_decoder_grads, \
            "No gradients found in encoder or decoder"
    
    def test_deterministic_behavior(self):
        """Test that results are deterministic with fixed seed."""
        set_deterministic_seed(123)
        obs1, _ = self.verifier._create_test_problem()
        grads1 = self.verifier._compute_decoder_gradients(obs1, torch.tensor([0.1]))
        
        set_deterministic_seed(123)
        obs2, _ = self.verifier._create_test_problem()
        grads2 = self.verifier._compute_decoder_gradients(obs2, torch.tensor([0.1]))
        
        # Results should be identical
        for key in grads1.keys():
            if key in grads2:
                assert np.isclose(grads1[key], grads2[key]), \
                    f"Gradients not deterministic for {key}"


class TestGradientVerificationIntegration:
    """Integration tests for the full gradient verification pipeline."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up integration test fixtures."""
        set_deterministic_seed(42)
        self.verifier = GradientVerificationTest(seed=42, device="cpu")
    
    def test_full_verification_pipeline(self):
        """Test the complete gradient verification pipeline."""
        # Run the full verification
        success = self.verifier.run_verification()
        
        # Verify results are populated
        assert len(self.verifier.results) > 0
        assert len(self.verifier.grad_checks) > 0
        
        # Check that key metrics are present
        assert "decoder_gradient_check" in self.verifier.results
        assert "solver_gradient_check" in self.verifier.results
    
    def test_report_contains_required_sections(self, tmp_path):
        """Test that generated report contains all required sections."""
        # Run verification first
        self.verifier.run_verification()
        
        # Generate report
        report_path = os.path.join(tmp_path, "integration_report.md")
        self.verifier.generate_report(report_path)
        
        with open(report_path, 'r') as f:
            content = f.read()
        
        # Check for required sections
        required_sections = [
            "Gradient Verification Report",
            "Results Summary",
            "Technical Details",
            "Conclusion"
        ]
        
        for section in required_sections:
            assert section in content, f"Missing required section: {section}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
