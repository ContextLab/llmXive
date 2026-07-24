"""
Unit tests for the ExplanationGenerator orchestrator.
Tests integration of neural, symbolic, and neuro-symbolic generators.
"""
import pytest
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from generate.explanation_generator import ExplanationGenerator
from generate.symbolic_explanation import SymbolicSolver
from generate.neural_explanation import NeuralExplanationGenerator
from generate.neuro_symbolic_explanation import NeuroSymbolicExplanationGenerator


class TestExplanationGenerator:
    """Tests for the ExplanationGenerator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, "output")
        self.problem_id = "test_problem_001"
        self.problem_data = {
            "id": self.problem_id,
            "type": "algebra",
            "question": "Solve for x: 2x + 4 = 10",
            "solution": "x = 3"
        }

    def teardown_method(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test ExplanationGenerator initialization."""
        generator = ExplanationGenerator(output_dir=self.output_dir)
        assert generator.output_dir == self.output_dir
        assert isinstance(generator.symbolic_gen, SymbolicSolver)
        assert isinstance(generator.neural_gen, NeuralExplanationGenerator)
        assert isinstance(generator.neuro_symbolic_gen, NeuroSymbolicExplanationGenerator)

    @patch.object(SymbolicSolver, 'solve', return_value={"trace": [{"rule": "subtract", "step": 1}], "solution": "x=3"})
    @patch.object(NeuralExplanationGenerator, 'generate', return_value="To solve this, we subtract 4 from both sides.")
    def test_generate_symbolic_only(self, mock_neural, mock_symbolic):
        """Test generating only the symbolic explanation."""
        generator = ExplanationGenerator(output_dir=self.output_dir)
        result = generator.generate_explanations(
            problem=self.problem_data,
            generate_neural=False,
            generate_symbolic=True,
            generate_neuro_symbolic=False
        )

        assert "symbolic" in result
        assert result["symbolic"]["trace"] == [{"rule": "subtract", "step": 1}]
        mock_symbolic.assert_called_once()
        mock_neural.assert_not_called()

    @patch.object(SymbolicSolver, 'solve', return_value={"trace": [{"rule": "subtract", "step": 1}], "solution": "x=3"})
    @patch.object(NeuralExplanationGenerator, 'generate', return_value="To solve this, we subtract 4 from both sides.")
    def test_generate_neural_only(self, mock_neural, mock_symbolic):
        """Test generating only the neural explanation."""
        generator = ExplanationGenerator(output_dir=self.output_dir)
        result = generator.generate_explanations(
            problem=self.problem_data,
            generate_neural=True,
            generate_symbolic=False,
            generate_neuro_symbolic=False
        )

        assert "neural" in result
        assert result["neural"] == "To solve this, we subtract 4 from both sides."
        mock_neural.assert_called_once()
        mock_symbolic.assert_not_called()

    @patch.object(SymbolicSolver, 'solve', return_value={"trace": [{"rule": "subtract", "step": 1}], "solution": "x=3"})
    @patch.object(NeuralExplanationGenerator, 'generate', return_value="To solve this, we subtract 4 from both sides.")
    def test_generate_neuro_symbolic(self, mock_neural, mock_symbolic):
        """Test generating the neuro-symbolic explanation."""
        generator = ExplanationGenerator(output_dir=self.output_dir)
        result = generator.generate_explanations(
            problem=self.problem_data,
            generate_neural=True,
            generate_symbolic=True,
            generate_neuro_symbolic=True
        )

        assert "neuro_symbolic" in result
        # Verify both underlying generators were called
        assert mock_symbolic.called
        assert mock_neural.called

    @patch.object(SymbolicSolver, 'solve', side_effect=Exception("Solver error"))
    def test_symbolic_failure_handling(self, mock_symbolic):
        """Test handling of symbolic generation failure."""
        generator = ExplanationGenerator(output_dir=self.output_dir)
        with pytest.raises(Exception):
            generator.generate_explanations(
                problem=self.problem_data,
                generate_symbolic=True,
                generate_neural=False,
                generate_neuro_symbolic=False
            )

    @patch.object(SymbolicSolver, 'solve', return_value={"trace": [], "solution": "x=3"})
    @patch.object(NeuralExplanationGenerator, 'generate', return_value="Explanation text")
    def test_save_artifacts(self, mock_neural, mock_symbolic):
        """Test that artifacts are saved to disk."""
        generator = ExplanationGenerator(output_dir=self.output_dir)
        result = generator.generate_explanations(
            problem=self.problem_data,
            generate_neural=True,
            generate_symbolic=True,
            generate_neuro_symbolic=True,
            save_to_disk=True
        )

        # Check files exist
        assert os.path.exists(os.path.join(self.output_dir, f"{self.problem_id}_neural.txt"))
        assert os.path.exists(os.path.join(self.output_dir, f"{self.problem_id}_symbolic.json"))
        assert os.path.exists(os.path.join(self.output_dir, f"{self.problem_id}_neuro_symbolic.txt"))

    def test_empty_problem_handling(self):
        """Test handling of empty or invalid problem data."""
        generator = ExplanationGenerator(output_dir=self.output_dir)
        with pytest.raises(ValueError):
            generator.generate_explanations(
                problem={},
                generate_neural=True,
                generate_symbolic=True,
                generate_neuro_symbolic=True
            )
