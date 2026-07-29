import pytest
import json
import os
import tempfile
from pathlib import Path
from code.gatekeeper.pipeline import GatekeeperPipeline, run_baseline
from code.models import Query, MemoryChunk

class TestBaselinePipeline:
    def setup_method(self):
        """Create temporary data files for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_path = os.path.join(self.temp_dir, "test_data.jsonl")
        self.output_path = os.path.join(self.temp_dir, "baseline_results.json")
        
        # Create a mock dataset file
        mock_data = [
            {
                "id": "test-001",
                "query": "What is the patient's history?",
                "role": "doctor",
                "domain": "medical",
                "leak_target": True,
                "memory_chunks": [
                    {"id": "m1", "text": "Patient has a history of diabetes.", "role": "nurse"},
                    {"id": "m2", "text": "Patient's name is John Doe.", "role": "admin"}
                ]
            },
            {
                "id": "test-002",
                "query": "Summarize the meeting.",
                "role": "manager",
                "domain": "office",
                "leak_target": False,
                "memory_chunks": [
                    {"id": "m3", "text": "Q3 targets discussed.", "role": "hr"}
                ]
            }
        ]
        
        with open(self.data_path, "w") as f:
            for item in mock_data:
                f.write(json.dumps(item) + "\n")

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_baseline_retrieval_output_structure(self):
        """Test that baseline retrieval produces valid JSON output with required fields."""
        pipeline = GatekeeperPipeline({"use_classifier": False})
        pipeline.load_components()
        
        results = pipeline.run_baseline_retrieval(
            data_path=self.data_path,
            output_path=self.output_path,
            domain_filter=["medical", "office"]
        )
        
        assert len(results) == 2
        
        # Check output file exists and is valid JSON
        assert os.path.exists(self.output_path)
        with open(self.output_path, "r") as f:
            saved_results = json.load(f)
        
        assert isinstance(saved_results, list)
        assert len(saved_results) == 2
        
        # Verify required fields
        for res in saved_results:
            assert "method" in res
            assert res["method"] == "Baseline-Retrieval"
            assert "allowed" in res
            assert res["allowed"] is True
            assert "domain" in res
            assert "id" in res

    def test_baseline_long_context_output_structure(self):
        """Test that baseline long-context produces valid JSON output."""
        pipeline = GatekeeperPipeline({"use_classifier": False})
        pipeline.load_components()
        
        results = pipeline.run_baseline_long_context(
            data_path=self.data_path,
            output_path=self.output_path,
            domain_filter=["medical"]
        )
        
        assert len(results) == 1
        
        with open(self.output_path, "r") as f:
            saved_results = json.load(f)
        
        for res in saved_results:
            assert res["method"] == "Baseline-LongContext"
            assert res["allowed"] is True
            assert res["domain"] == "medical"

    def test_baseline_uses_identical_retrieval_params(self):
        """
        Verify that baseline runs use the same data and context construction 
        as the Gatekeeper run (no filtering of context chunks).
        """
        # Run Gatekeeper
        pipeline = GatekeeperPipeline({"use_classifier": False})
        pipeline.load_components()
        
        gate_results = pipeline.run_gatekeeper(
            data_path=self.data_path,
            output_path=os.path.join(self.temp_dir, "gate_results.json"),
            domain_filter=["medical"]
        )
        
        # Run Baseline
        base_results = pipeline.run_baseline_retrieval(
            data_path=self.data_path,
            output_path=os.path.join(self.temp_dir, "base_results.json"),
            domain_filter=["medical"]
        )
        
        # Both should process the same number of items
        assert len(gate_results) == len(base_results)
        
        # IDs should match
        gate_ids = {r.id for r in gate_results}
        base_ids = {r.id for r in base_results}
        assert gate_ids == base_ids

    def test_baseline_allows_unauthorized_access(self):
        """
        Verify that baseline allows access even when role might be unauthorized
        (since baseline has no access control).
        """
        pipeline = GatekeeperPipeline({"use_classifier": False})
        pipeline.load_components()
        
        results = pipeline.run_baseline_retrieval(
            data_path=self.data_path,
            output_path=self.output_path
        )
        
        for res in results:
            assert res["allowed"] is True
            assert "No access control" in res["reason"] or "Baseline" in res["reason"]
