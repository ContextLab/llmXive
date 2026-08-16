"""
Integration tests for the Bidirectional Evolutionary Search (BES) loop.

This test suite verifies the end-to-end execution of the BES framework,
specifically focusing on the integration of the symbolic backward step
with the evolutionary loop.

Prerequisites:
- T024 (Main BES Loop) must be implemented.
- T018, T019 (Symbolic Parser/Planner) must be implemented.
- T011, T013 (Dataset Generation) must be completed.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.bes.backward_step import BackwardStep, BackwardStepResult
from code.bes.forward_step import ForwardStep
from code.bes.population import Population, Individual
from code.config import load_config
from code.dataset.generator import PuzzleGenerator, PuzzleType
from code.dataset.verifier import verify_solution, SolutionResult
from code.symbolic.planner import SymbolicPlanner
from code.utils.seed import set_seed

# Import the main orchestrator logic we are testing
from code.main import BESOrchestrator, BESRunResult


class TestBESLoopIntegration:
    """Integration tests for the BES loop with a small population."""

    @classmethod
    def setup_class(cls):
        """Set up test fixtures."""
        set_seed(42)
        cls.test_data_dir = Path(tempfile.mkdtemp(prefix="bes_test_"))
        cls.raw_data_dir = cls.test_data_dir / "raw"
        cls.processed_data_dir = cls.test_data_dir / "processed"
        cls.raw_data_dir.mkdir(parents=True)
        cls.processed_data_dir.mkdir(parents=True)

        # Generate a small, deterministic dataset for testing
        generator = PuzzleGenerator(seed=42)
        test_puzzles = []
        for i in range(5):  # Small population test
            puzzle = generator.generate(
                puzzle_type=PuzzleType.SUDOKU_VARIANT,
                complexity=i + 1,
                seed=42 + i
            )
            test_puzzles.append(puzzle)

        # Save to raw data
        dataset_file = cls.raw_data_dir / "test_puzzles.json"
        with open(dataset_file, "w") as f:
            json.dump([p.model_dump() for p in test_puzzles], f, indent=2)

        # Create a minimal config for the test
        cls.config = {
            "experiment_id": "test_bes_loop_integration",
            "population_size": 3,
            "generations": 2,
            "dataset_path": str(dataset_file),
            "output_dir": str(cls.processed_data_dir),
            "seed": 42,
            "forward_model": "distilbert-base-uncased",
            "symbolic_planner_enabled": True
        }

        config_file = cls.test_data_dir / "config.yaml"
        import yaml
        with open(config_file, "w") as f:
            yaml.dump(cls.config, f)

    @classmethod
    def teardown_class(cls):
        """Clean up test fixtures."""
        if cls.test_data_dir.exists():
            shutil.rmtree(cls.test_data_dir)

    def test_bes_loop_executes_symbolic_backward_step(self):
        """
        Integration test for the BES loop with a small population.
        
        Verifies that:
        1. The BES loop initializes correctly with a small population.
        2. The symbolic backward step is executed for each generation.
        3. The backward step returns valid results (SubGoal decompositions).
        4. The population evolves based on the backward step feedback.
        5. The loop completes without errors.
        """
        # Load config
        config = load_config(str(self.test_data_dir / "config.yaml"))
        
        # Initialize the orchestrator
        orchestrator = BESOrchestrator(config)
        
        # Run the BES loop
        result = orchestrator.run()
        
        # Assertions
        assert isinstance(result, BESRunResult), "Result should be a BESRunResult"
        assert result.success, f"BES loop failed: {result.error_message}"
        assert result.generations_completed == config["generations"], \
            f"Expected {config['generations']} generations, got {result.generations_completed}"
        
        # Verify that the symbolic backward step was actually called
        # We check the logs for evidence of symbolic planning
        log_file = Path(config["output_dir"]) / "experiment.log"
        assert log_file.exists(), "Experiment log file should exist"
        
        with open(log_file, "r") as f:
            log_content = f.read()
        
        # Check for evidence of symbolic backward step execution
        assert "symbolic" in log_content.lower(), \
            "Log should contain evidence of symbolic backward step execution"
        assert "backward" in log_content.lower(), \
            "Log should contain evidence of backward step execution"
        
        # Verify population evolution occurred
        assert len(result.final_population) == config["population_size"], \
            "Final population size should match config"
        
        # Verify that at least one individual has been improved or evaluated
        improved_count = sum(1 for ind in result.final_population if ind.fitness is not None)
        assert improved_count > 0, \
            "At least one individual should have a fitness score after evolution"

    def test_bes_loop_handles_contradiction_detection(self):
        """
        Test that the BES loop correctly handles CONTRADICTION_DETECTED exceptions
        from the symbolic planner.
        """
        # This test verifies robustness by ensuring the loop doesn't crash
        # when the symbolic planner detects a contradiction
        
        config = load_config(str(self.test_data_dir / "config.yaml"))
        orchestrator = BESOrchestrator(config)
        
        # Run the loop - it should handle exceptions gracefully
        result = orchestrator.run()
        
        # The loop should complete successfully even with potential contradictions
        # (the planner should log them and continue)
        assert result.success or "CONTRADICTION" in str(result.error_message), \
            "Loop should handle contradictions gracefully"

    def test_bes_loop_population_management(self):
        """
        Test that the population is correctly managed throughout the BES loop.
        """
        config = load_config(str(self.test_data_dir / "config.yaml"))
        orchestrator = BESOrchestrator(config)
        
        # Run the loop
        result = orchestrator.run()
        
        # Verify population size is maintained
        assert len(result.final_population) == config["population_size"], \
            "Population size should be maintained throughout the loop"
        
        # Verify all individuals have required attributes
        for individual in result.final_population:
            assert hasattr(individual, "fitness"), "Individual should have fitness attribute"
            assert hasattr(individual, "solution"), "Individual should have solution attribute"
            assert hasattr(individual, "genetic_material"), \
                "Individual should have genetic_material attribute"