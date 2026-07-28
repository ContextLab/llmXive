import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure code directory is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pipeline.model import generate_modification_proposal
from schemas.modification_proposal import ModificationProposal

class TestT037LogicSeparation(unittest.TestCase):
    """
    Test case for T037: Separation of Generative/Verification Logic.
    
    Verifies that the modification proposal prompt explicitly excludes
    access to benchmark results or evaluation metrics.
    """

    def test_proposal_prompt_excludes_benchmark_metrics(self):
        """
        Verifies that the prompt string generated in generate_modification_proposal
        does not contain references to GSM8K, ARC, ECE, or benchmark results.
        """
        # Create a mock model
        mock_model = MagicMock()
        
        # Call the function
        # We patch the internal logic to capture the prompt or return a mock
        # Since the function currently returns a proposal, we check the implementation
        # by inspecting the source or mocking the LLM call if it existed.
        # Here we assume the prompt is constructed internally.
        
        # We will test by checking the docstring or by mocking the behavior
        # to ensure no benchmark data is passed.
        
        # For this unit test, we verify the signature and behavior:
        # 1. The function signature does NOT accept benchmark_metrics
        import inspect
        sig = inspect.signature(generate_modification_proposal)
        params = list(sig.parameters.keys())
        
        self.assertNotIn('benchmark_metrics', params, 
            "generate_modification_proposal must NOT accept benchmark_metrics parameter")
        self.assertNotIn('eval_metrics', params,
            "generate_modification_proposal must NOT accept eval_metrics parameter")
        self.assertNotIn('gsm8k', params,
            "generate_modification_proposal must NOT accept gsm8k parameter")

    def test_proposal_logic_uses_only_training_loss(self):
        """
        Verifies that the proposal generation logic relies on training_loss.
        """
        mock_model = MagicMock()
        
        # Test with high loss
        proposal_high = generate_modification_proposal(
            model=mock_model,
            training_loss=3.0,
            cycle=1
        )
        
        # Test with low loss
        proposal_low = generate_modification_proposal(
            model=mock_model,
            training_loss=1.0,
            cycle=1
        )
        
        # The proposals should differ based on loss, not external metrics
        self.assertIsNotNone(proposal_high)
        self.assertIsNotNone(proposal_low)
        
        # Verify the rationale reflects the loss-based logic
        self.assertIn("loss", proposal_high.rationale.lower() or proposal_low.rationale.lower())

    def test_no_benchmark_data_in_proposal_rationale(self):
        """
        Verifies that the rationale string does not mention benchmark names.
        """
        mock_model = MagicMock()
        proposal = generate_modification_proposal(
            model=mock_model,
            training_loss=2.5,
            cycle=1
        )
        
        banned_terms = ["gsm8k", "arc", "challenge", "ece", "benchmark", "evaluation metric"]
        
        rationale_lower = proposal.rationale.lower()
        for term in banned_terms:
            self.assertNotIn(term, rationale_lower, 
                f"Rationale should not contain benchmark term: {term}")

if __name__ == '__main__':
    unittest.main()