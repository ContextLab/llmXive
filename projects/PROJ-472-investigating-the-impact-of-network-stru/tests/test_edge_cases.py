"""
Unit tests for edge cases in metrics, quality control, and fitting modules.

This module verifies that:
1. `metrics.py` correctly handles disconnected graphs (sparse connectivity).
2. `quality_control.py` correctly identifies and excludes participants with disconnected graphs.
3. `fitting.py` correctly handles power-law convergence failures by logging errors and excluding participants.

Dependencies: T010, T012, T033
"""

import os
import sys
import logging
import tempfile
import json
import numpy as np
import pandas as pd
import networkx as nx
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.analysis import metrics, fitting
from code.data import quality_control
from code.utils.logger import setup_logger

# Setup logger for tests
logger = setup_logger("test_edge_cases", level=logging.DEBUG)


class TestDisconnectedGraphsMetrics:
    """Tests for metrics.py handling of disconnected graphs."""

    def test_compute_degree_centrality_disconnected_graph(self):
        """Verify degree centrality handles disconnected components."""
        # Create a disconnected graph: two separate cliques
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4, 5, 6])
        G.add_edges_from([(1, 2), (2, 3), (1, 3)])  # Component 1
        G.add_edges_from([(4, 5), (5, 6), (4, 6)])  # Component 2
        
        # Should not raise an error
        result = metrics.compute_degree_centrality(G)
        
        # Verify all nodes have non-negative centrality
        assert len(result) == 6
        for node, centrality in result.items():
            assert centrality >= 0.0
        
        # Nodes in different components should have different centralities
        # (unless the components are identical in structure)
        logger.info(f"Degree centrality for disconnected graph: {result}")

    def test_compute_clustering_coefficient_disconnected_graph(self):
        """Verify clustering coefficient handles disconnected components."""
        # Create a disconnected graph
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4, 5, 6])
        G.add_edges_from([(1, 2), (2, 3), (1, 3)])  # Component 1
        G.add_edges_from([(4, 5), (5, 6), (4, 6)])  # Component 2
        
        # Should not raise an error
        result = metrics.compute_clustering_coefficient(G)
        
        # Verify all nodes have valid clustering coefficients
        assert len(result) == 6
        for node, coeff in result.items():
            assert 0.0 <= coeff <= 1.0
        
        logger.info(f"Clustering coefficient for disconnected graph: {result}")

    def test_compute_rich_club_coefficient_disconnected_graph(self):
        """Verify rich-club coefficient handles disconnected components."""
        # Create a disconnected graph with varying degrees
        G = nx.Graph()
        # Component 1: High degree nodes
        G.add_nodes_from([1, 2, 3, 4, 5])
        G.add_edges_from([
            (1, 2), (1, 3), (1, 4), (1, 5),  # Node 1 connects to all
            (2, 3), (2, 4), (2, 5),
            (3, 4), (3, 5),
            (4, 5)
        ])
        # Component 2: Low degree nodes
        G.add_nodes_from([6, 7, 8])
        G.add_edges_from([(6, 7), (7, 8)])
        
        # Should not raise an error
        result = metrics.compute_rich_club_coefficient(G)
        
        # Verify result is a dictionary
        assert isinstance(result, dict)
        assert len(result) > 0
        
        # Verify coefficients are in valid range
        for k, coeff in result.items():
            assert 0.0 <= coeff <= 1.0
        
        logger.info(f"Rich-club coefficient for disconnected graph: {result}")

    def test_run_metrics_pipeline_disconnected_graph(self):
        """Verify the full metrics pipeline handles disconnected graphs."""
        # Create a disconnected graph
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4, 5, 6])
        G.add_edges_from([(1, 2), (2, 3), (1, 3)])  # Component 1
        G.add_edges_from([(4, 5), (5, 6), (4, 6)])  # Component 2
        
        # Mock the adjacency matrix loading
        with tempfile.TemporaryDirectory() as tmpdir:
            matrix_path = Path(tmpdir) / "connectome.npy"
            np.save(matrix_path, nx.to_numpy_array(G))
            
            subject_id = "test_disconnected"
            metrics_dir = Path(tmpdir) / "metrics"
            metrics_dir.mkdir()
            
            # Run the pipeline
            result = metrics.run_metrics_pipeline(
                subject_id=subject_id,
                adjacency_matrix_path=str(matrix_path),
                output_dir=str(metrics_dir)
            )
            
            # Verify result contains expected keys
            assert "degree" in result
            assert "clustering" in result
            assert "rich_club" in result
            
            # Verify no NaN values were introduced
            for key, values in result.items():
                if isinstance(values, dict):
                    for v in values.values():
                        assert not np.isnan(v)
                elif isinstance(values, (list, np.ndarray)):
                    assert not np.any(np.isnan(values))
            
            logger.info(f"Metrics pipeline result for disconnected graph: {result}")


class TestDisconnectedGraphsQualityControl:
    """Tests for quality_control.py handling of disconnected graphs."""

    def test_check_graph_connectivity_disconnected(self):
        """Verify that disconnected graphs are correctly identified."""
        # Create a disconnected graph
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4, 5, 6])
        G.add_edges_from([(1, 2), (2, 3), (1, 3)])  # Component 1
        G.add_edges_from([(4, 5), (5, 6), (4, 6)])  # Component 2
        
        # Check connectivity
        is_connected, num_components = quality_control.check_graph_connectivity(G)
        
        # Verify results
        assert is_connected is False
        assert num_components == 2
        
        logger.info(f"Connectivity check for disconnected graph: connected={is_connected}, components={num_components}")

    def test_check_graph_connectivity_connected(self):
        """Verify that connected graphs are correctly identified."""
        # Create a connected graph
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4, 5])
        G.add_edges_from([(1, 2), (2, 3), (3, 4), (4, 5), (1, 5)])
        
        # Check connectivity
        is_connected, num_components = quality_control.check_graph_connectivity(G)
        
        # Verify results
        assert is_connected is True
        assert num_components == 1
        
        logger.info(f"Connectivity check for connected graph: connected={is_connected}, components={num_components}")

    def test_run_qc_for_subject_disconnected_graph(self):
        """Verify that QC correctly flags disconnected graphs."""
        # Create a disconnected graph
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4, 5, 6])
        G.add_edges_from([(1, 2), (2, 3), (1, 3)])  # Component 1
        G.add_edges_from([(4, 5), (5, 6), (4, 6)])  # Component 2
        
        with tempfile.TemporaryDirectory() as tmpdir:
            matrix_path = Path(tmpdir) / "connectome.npy"
            np.save(matrix_path, nx.to_numpy_array(G))
            
            subject_id = "test_disconnected_qc"
            output_dir = Path(tmpdir) / "qc"
            output_dir.mkdir()
            
            # Run QC
            qc_result = quality_control.run_qc_for_subject(
                subject_id=subject_id,
                adjacency_matrix_path=str(matrix_path),
                output_dir=str(output_dir)
            )
            
            # Verify QC flags the graph as disconnected
            assert "is_connected" in qc_result
            assert qc_result["is_connected"] is False
            assert "num_components" in qc_result
            assert qc_result["num_components"] == 2
            
            # Verify the result indicates the participant should be excluded
            assert "exclude" in qc_result
            assert qc_result["exclude"] is True
            
            logger.info(f"QC result for disconnected graph: {qc_result}")

    def test_calculate_pipeline_completeness_with_disconnected(self):
        """Verify that pipeline completeness accounts for disconnected graphs."""
        # Mock data: some subjects have disconnected graphs
        qc_results = [
            {"subject_id": "S1", "is_connected": True, "exclude": False},
            {"subject_id": "S2", "is_connected": False, "exclude": True},
            {"subject_id": "S3", "is_connected": True, "exclude": False},
            {"subject_id": "S4", "is_connected": False, "exclude": True},
        ]
        
        # Calculate completeness
        completeness = quality_control.calculate_pipeline_completeness(qc_results)
        
        # Verify completeness calculation
        total = len(qc_results)
        complete = sum(1 for r in qc_results if not r["exclude"])
        expected_completeness = complete / total
        
        assert completeness == expected_completeness
        assert completeness == 0.5  # 2 out of 4 are complete
        
        logger.info(f"Pipeline completeness with disconnected graphs: {completeness}")


class TestPowerLawConvergenceFitting:
    """Tests for fitting.py handling of power-law convergence failures."""

    def test_fit_power_law_model_convergence_failure(self):
        """Verify that convergence failures are handled gracefully."""
        # Create a dataset that will likely cause convergence failure
        # (e.g., very small sample, all zeros, or highly irregular)
        with patch("powerlaw.Fit") as mock_fit:
            # Mock the Fit object to raise a convergence error
            mock_fit_instance = MagicMock()
            mock_fit_instance.power_law.log_likelihood_ratio.return_value = (float('inf'), float('inf'))
            mock_fit_instance.power_law.p_value.return_value = 0.0
            
            # Simulate a convergence failure by raising an exception during fit
            mock_fit.side_effect = Exception("Convergence failed: Maximum iterations reached")
            
            # Create a temporary file with invalid data
            with tempfile.TemporaryDirectory() as tmpdir:
                data_path = Path(tmpdir) / "invalid_avalanches.csv"
                # Create data that will likely cause issues
                df = pd.DataFrame({"size": [1, 1, 1, 1, 1]})
                df.to_csv(data_path, index=False)
                
                subject_id = "test_convergence_fail"
                
                # Run fitting - should handle the error gracefully
                result = fitting.run_fitting_for_subject(
                    subject_id=subject_id,
                    avalanche_data_path=str(data_path),
                    output_dir=tmpdir
                )
                
                # Verify the result indicates failure
                assert result["status"] == "failed"
                assert "error" in result
                assert "Convergence" in result["error"] or "convergence" in result["error"].lower()
                
                # Verify the participant is excluded from further analysis
                assert result["exclude_from_analysis"] is True
                
                logger.info(f"Fitting result for convergence failure: {result}")

    def test_fit_power_law_model_success(self):
        """Verify that successful fits are handled correctly."""
        # Create a dataset that follows a power-law distribution
        # Using a simple power-law with alpha = 2.5
        np.random.seed(42)
        valid_sizes = np.random.pareto(1.5, 1000) + 1  # Pareto is power-law
        valid_sizes = np.floor(valid_sizes).astype(int)
        valid_sizes = valid_sizes[valid_sizes > 0]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "valid_avalanches.csv"
            df = pd.DataFrame({"size": valid_sizes})
            df.to_csv(data_path, index=False)
            
            subject_id = "test_convergence_success"
            
            # Run fitting
            result = fitting.run_fitting_for_subject(
                subject_id=subject_id,
                avalanche_data_path=str(data_path),
                output_dir=tmpdir
            )
            
            # Verify the result indicates success
            assert result["status"] == "success"
            assert "exclude_from_analysis" not in result or result.get("exclude_from_analysis") is False
            
            # Verify key fitting parameters are present
            assert "alpha" in result
            assert "xmin" in result
            assert "log_likelihood" in result
            
            logger.info(f"Fitting result for successful fit: alpha={result['alpha']}, xmin={result['xmin']}")

    def test_run_fitting_pipeline_with_mixed_results(self):
        """Verify that the pipeline handles a mix of success and failure cases."""
        # Create mock data for multiple subjects
        with tempfile.TemporaryDirectory() as tmpdir:
            # Subject 1: Valid data
            data1 = Path(tmpdir) / "sub1_avalanches.csv"
            pd.DataFrame({"size": np.random.pareto(1.5, 100) + 1}).to_csv(data1, index=False)
            
            # Subject 2: Invalid data (all same value)
            data2 = Path(tmpdir) / "sub2_avalanches.csv"
            pd.DataFrame({"size": [1] * 100}).to_csv(data2, index=False)
            
            # Create a mock for the data loading function
            def mock_load_data(subject_id):
                if subject_id == "sub1":
                    return data1
                elif subject_id == "sub2":
                    return data2
                else:
                    raise FileNotFoundError(f"Data for {subject_id} not found")
            
            with patch("code.analysis.fitting.load_avalanche_sizes_from_store", side_effect=mock_load_data):
                output_dir = Path(tmpdir) / "fitting_results"
                output_dir.mkdir()
                
                subject_ids = ["sub1", "sub2"]
                
                # Run the pipeline
                results = fitting.run_fitting_pipeline(
                    subject_ids=subject_ids,
                    output_dir=str(output_dir)
                )
                
                # Verify results contain both success and failure
                assert len(results) == 2
                
                sub1_result = next(r for r in results if r["subject_id"] == "sub1")
                sub2_result = next(r for r in results if r["subject_id"] == "sub2")
                
                # Sub1 should succeed
                assert sub1_result["status"] == "success"
                
                # Sub2 should fail
                assert sub2_result["status"] == "failed"
                assert sub2_result["exclude_from_analysis"] is True
                
                logger.info(f"Fitting pipeline results: {results}")

    def test_generate_fitting_report_with_failures(self):
        """Verify that the report generation handles failures correctly."""
        # Create a list of fitting results with mixed outcomes
        results = [
            {
                "subject_id": "S1",
                "status": "success",
                "alpha": 2.5,
                "xmin": 5,
                "exclude_from_analysis": False
            },
            {
                "subject_id": "S2",
                "status": "failed",
                "error": "Convergence failed",
                "exclude_from_analysis": True
            },
            {
                "subject_id": "S3",
                "status": "success",
                "alpha": 2.3,
                "xmin": 4,
                "exclude_from_analysis": False
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "fitting_report.json"
            
            # Generate report
            fitting.generate_fitting_report(results, str(report_path))
            
            # Verify report was created
            assert report_path.exists()
            
            # Load and verify report content
            with open(report_path, 'r') as f:
                report = json.load(f)
            
            assert "total_subjects" in report
            assert report["total_subjects"] == 3
            
            assert "successful_fits" in report
            assert report["successful_fits"] == 2
            
            assert "failed_fits" in report
            assert report["failed_fits"] == 1
            
            assert "excluded_subjects" in report
            assert report["excluded_subjects"] == ["S2"]
            
            logger.info(f"Fitting report: {report}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])