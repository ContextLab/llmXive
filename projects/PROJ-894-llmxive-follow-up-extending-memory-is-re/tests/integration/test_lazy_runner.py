import os
import json
import csv
import pytest
from pathlib import Path
import tempfile
import shutil

# Import runner functionality
from runner import run_batch, load_tasks, load_graph, TaskResult
from strategies.lazy import run_lazy_strategy

class TestLazyRunner:
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test artifacts."""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)

    @pytest.fixture
    def sample_tasks(self, temp_dir):
        """Create sample task data."""
        tasks = [
            {
                "task_id": "test_001",
                "question": "What is the capital of France?",
                "context": "Paris is the capital and largest city of France. It is located in the north-central part of the country.",
                "answer": "Paris"
            },
            {
                "task_id": "test_002",
                "question": "Who wrote Romeo and Juliet?",
                "context": "Romeo and Juliet is a tragedy written by William Shakespeare early in his career about two young star-crossed lovers.",
                "answer": "William Shakespeare"
            }
        ]
        
        tasks_path = os.path.join(temp_dir, "tasks.jsonl")
        with open(tasks_path, 'w', encoding='utf-8') as f:
            for task in tasks:
                f.write(json.dumps(task) + '\n')
        
        return tasks_path

    @pytest.fixture
    def sample_graph(self, temp_dir):
        """Create sample graph data."""
        graph_data = {
            "test_001": [
                {"source": "Paris", "target": "France", "relation": "capital_of"},
                {"source": "Paris", "target": "North-Central", "relation": "located_in"}
            ],
            "test_002": [
                {"source": "Romeo", "target": "Juliet", "relation": "loves"},
                {"source": "William Shakespeare", "target": "Romeo and Juliet", "relation": "wrote"}
            ]
        }
        
        graph_path = os.path.join(temp_dir, "graph.json")
        with open(graph_path, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f)
        
        return graph_path

    @pytest.fixture
    def output_path(self, temp_dir):
        """Return output path for results."""
        return os.path.join(temp_dir, "results.csv")

    def test_lazy_runner_creates_csv(self, sample_tasks, sample_graph, output_path):
        """Test that lazy runner creates the output CSV file."""
        # Load graph data
        graph_data = load_graph(sample_graph, is_noisy=False)
        
        # Load tasks
        tasks = load_tasks(sample_tasks)
        
        # Run lazy strategy
        run_batch(
            tasks=tasks,
            graph_data=graph_data,
            strategy='lazy',
            output_path=output_path,
            threshold=0.7,
            timeout=30
        )
        
        # Verify file exists
        assert os.path.exists(output_path), "Output CSV file was not created"
        
        # Verify file is not empty
        assert os.path.getsize(output_path) > 0, "Output CSV file is empty"

    def test_lazy_runner_csv_schema(self, sample_tasks, sample_graph, output_path):
        """Test that lazy runner CSV has correct schema."""
        graph_data = load_graph(sample_graph, is_noisy=False)
        tasks = load_tasks(sample_tasks)
        
        run_batch(
            tasks=tasks,
            graph_data=graph_data,
            strategy='lazy',
            output_path=output_path,
            threshold=0.7,
            timeout=30
        )
        
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            
            # Required fields
            required_fields = ['task_id', 'strategy', 'accuracy', 'nodes_visited', 
                             'latency_ms', 'status', 'evidence_threshold']
            
            for field in required_fields:
                assert field in fieldnames, f"Missing required field: {field}"
            
            # Check evidence_threshold is present
            assert 'evidence_threshold' in fieldnames, "evidence_threshold field missing"

    def test_lazy_runner_evidence_threshold_format(self, sample_tasks, sample_graph, output_path):
        """Test that evidence_threshold is formatted to 2 decimal places."""
        graph_data = load_graph(sample_graph, is_noisy=False)
        tasks = load_tasks(sample_tasks)
        
        threshold = 0.7
        run_batch(
            tasks=tasks,
            graph_data=graph_data,
            strategy='lazy',
            output_path=output_path,
            threshold=threshold,
            timeout=30
        )
        
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                threshold_val = row['evidence_threshold']
                # Check it's a valid float with 2 decimal places
                float(threshold_val)  # Should not raise
                assert '.' in threshold_val, "Evidence threshold should have decimal point"
                decimal_part = threshold_val.split('.')[1]
                assert len(decimal_part) <= 2, "Evidence threshold should have at most 2 decimal places"

    def test_lazy_runner_status_values(self, sample_tasks, sample_graph, output_path):
        """Test that status values are valid."""
        graph_data = load_graph(sample_graph, is_noisy=False)
        tasks = load_tasks(sample_tasks)
        
        run_batch(
            tasks=tasks,
            graph_data=graph_data,
            strategy='lazy',
            output_path=output_path,
            threshold=0.7,
            timeout=30
        )
        
        valid_statuses = ['COMPLETED', 'TIMEOUT', 'DEGENERATE', 'UNRESOLVED', 'ERROR']
        
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                status = row['status']
                assert status in valid_statuses, f"Invalid status value: {status}"

    def test_lazy_runner_task_ids_match(self, sample_tasks, sample_graph, output_path):
        """Test that all task IDs from input appear in output."""
        graph_data = load_graph(sample_graph, is_noisy=False)
        tasks = load_tasks(sample_tasks)
        input_task_ids = {task['task_id'] for task in tasks}
        
        run_batch(
            tasks=tasks,
            graph_data=graph_data,
            strategy='lazy',
            output_path=output_path,
            threshold=0.7,
            timeout=30
        )
        
        output_task_ids = set()
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                output_task_ids.add(row['task_id'])
        
        assert input_task_ids == output_task_ids, "Task IDs in output don't match input"

    def test_lazy_runner_accuracy_values(self, sample_tasks, sample_graph, output_path):
        """Test that accuracy values are numeric and in valid range."""
        graph_data = load_graph(sample_graph, is_noisy=False)
        tasks = load_tasks(sample_tasks)
        
        run_batch(
            tasks=tasks,
            graph_data=graph_data,
            strategy='lazy',
            output_path=output_path,
            threshold=0.7,
            timeout=30
        )
        
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                accuracy = float(row['accuracy'])
                assert 0.0 <= accuracy <= 1.0, f"Accuracy out of range: {accuracy}"

    def test_lazy_runner_nodes_visited_positive(self, sample_tasks, sample_graph, output_path):
        """Test that nodes_visited values are non-negative."""
        graph_data = load_graph(sample_graph, is_noisy=False)
        tasks = load_tasks(sample_tasks)
        
        run_batch(
            tasks=tasks,
            graph_data=graph_data,
            strategy='lazy',
            output_path=output_path,
            threshold=0.7,
            timeout=30
        )
        
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                nodes = int(row['nodes_visited'])
                assert nodes >= 0, f"Nodes visited should be non-negative: {nodes}"
