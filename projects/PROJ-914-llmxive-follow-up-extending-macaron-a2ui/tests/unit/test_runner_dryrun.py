import pytest
import pandas as pd
import os
import tempfile
from pathlib import Path

# Import the functions we are testing
from simulation.runner import MockGenerativeModel, load_annotated_data, simulate_interaction, run_simulation, save_simulation_results
from data.models import SimulationRun

class TestMockGenerativeModel:
    def test_initialization(self):
        model = MockGenerativeModel(seed=42)
        assert model.name == "MockGenerativeModel"

    def test_generate_ui(self):
        model = MockGenerativeModel()
        result = model.generate_ui("Test query", complexity=5)
        
        assert "ui_elements" in result
        assert "element_count" in result
        assert "generation_time_ms" in result
        assert result["element_count"] == 2
        assert isinstance(result["generation_time_ms"], int)

class TestLoadAnnotatedData:
    def test_load_from_file(self):
        # Create a temporary CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("query,ground_truth_intent,complexity_score\n")
            f.write("Hello,High-Confidence,3\n")
            f.write("World,Ambiguous,5\n")
            temp_path = f.name

        try:
            df = load_annotated_data(temp_path)
            assert len(df) == 2
            assert "query" in df.columns
            assert "ground_truth_intent" in df.columns
            assert "complexity_score" in df.columns
        finally:
            os.unlink(temp_path)

    def test_missing_file(self):
        with pytest.raises(FileNotFoundError):
            load_annotated_data("/nonexistent/path.csv")

    def test_missing_columns(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("query,other_col\n")
            f.write("Hello,World\n")
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                load_annotated_data(temp_path)
        finally:
            os.unlink(temp_path)

class TestSimulateInteraction:
    def test_simulate_interaction_dry_run(self):
        model = MockGenerativeModel()
        row = {
            "query": "Test query",
            "ground_truth_intent": "High-Confidence",
            "complexity_score": 3
        }
        
        run = simulate_interaction(row, model, dry_run=True, simulate_delay=False)
        
        assert isinstance(run, SimulationRun)
        assert run.query == "Test query"
        assert run.ground_truth_intent == "High-Confidence"
        assert run.total_latency_ms >= 0
        assert run.abandoned == False # With default patience and low latency

    def test_simulate_interaction_abandoned(self):
        model = MockGenerativeModel()
        row = {
            "query": "Test query",
            "ground_truth_intent": "High-Confidence",
            "complexity_score": 100 # High complexity -> higher latency
        }
        
        # We can't easily force abandonment without mocking patience,
        # but we can check that the logic runs without error.
        run = simulate_interaction(row, model, dry_run=True, simulate_delay=True)
        
        assert isinstance(run, SimulationRun)

class TestRunSimulation:
    def test_run_simulation_sample(self):
        # Create a small dataframe
        df = pd.DataFrame({
            "query": ["Q1", "Q2"],
            "ground_truth_intent": ["High", "Ambiguous"],
            "complexity_score": [1, 2]
        })
        
        results = run_simulation(df, dry_run=True, sample_size=2)
        
        assert len(results) == 2
        assert all(isinstance(r, SimulationRun) for r in results)

class TestSaveSimulationResults:
    def test_save_results(self):
        results = [
            SimulationRun(
                id="1",
                timestamp=None, # Simplified for test
                query="Test",
                ground_truth_intent="High",
                routing_decision=None, # Simplified
                patience_threshold=2.0,
                total_latency_ms=100,
                abandoned=False,
                ui_elements=[],
                ui_element_count=1,
                alignment_score=0.9
            )
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            temp_path = f.name
        
        try:
            save_simulation_results(results, temp_path)
            assert os.path.exists(temp_path)
            
            df = pd.read_csv(temp_path)
            assert len(df) == 1
            assert df.iloc[0]['query'] == "Test"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)