"""
Integration tests for the full pipeline (mocked data).
"""
import pytest
from pathlib import Path
import numpy as np

# Import pipeline components
from code.ingest import SyntheticDataGenerator, DefectGraphBuilder
from code.metrics import MetricCalculator
from code.config import Config, RunMode

@pytest.mark.integration
def test_synthetic_to_metrics_pipeline(tmp_path):
    """Test that synthetic data flows through graph builder to metrics."""
    # Setup
    config = Config(project_root=tmp_path)
    generator = SyntheticDataGenerator(seed=42)
    builder = DefectGraphBuilder()
    calculator = MetricCalculator()

    # Generate synthetic snapshot
    snapshot = generator.generate_snapshot(n_atoms=50, composition={"Cu": 0.5, "Ni": 0.5})
    
    # Build graph
    graph = builder.build_graph(snapshot)
    
    assert graph.node_count > 0
    assert len(graph.adjacency_list) == graph.node_count

    # Calculate metrics
    metrics = calculator.calculate(graph)
    
    assert "clustering_coefficient" in metrics
    assert "mean_degree" in metrics
    assert metrics["mean_degree"] > 0

@pytest.mark.integration
def test_empty_graph_handling(tmp_path):
    """Test that the pipeline handles edge cases (e.g., single atom)."""
    from code.models import AtomicSnapshot, DefectGraph
    from code.ingest import DefectGraphBuilder
    from code.metrics import MetricCalculator

    # Create a single-atom snapshot
    snapshot = AtomicSnapshot(
        snapshot_id="edge_case_001",
        species=["Cu"],
        positions=np.array([[0.0, 0.0, 0.0]]),
        cell=np.array([[2.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 2.0]]),
        metadata={"temperature": 300}
    )

    builder = DefectGraphBuilder()
    graph = builder.build_graph(snapshot)
    
    # Should handle gracefully (0 edges)
    assert graph.node_count == 1
    assert graph.edge_count == 0

    calculator = MetricCalculator()
    metrics = calculator.calculate(graph)
    
    # Metrics should be defined (possibly NaN or 0)
    assert "mean_degree" in metrics
