import json
import pytest
from pathlib import Path
import tempfile
import os

# Mock the analysis modules to avoid heavy imports if necessary, 
# but here we assume the modules exist as per task requirements.
# We will test the logic functions directly if possible, or via the main entry.

def test_map_feature_ranks_logic():
    """Test the core mapping logic of FR-009."""
    from analysis.comparative_mapping import map_feature_ranks

    # Mock RF Data
    rf_data = {
        "feature_importance": [
            {"feature": "MW", "mean_abs_shap_value": 0.5},
            {"feature": "logP", "mean_abs_shap_value": 0.3},
            {"feature": "TPSA", "mean_abs_shap_value": 0.1}
        ]
    }

    # Mock GNN Data
    gnn_data = {
        "substructure_importance": [
            {"substructure_id": "aromatic_ring", "description": "Benzene ring", "importance_score": 0.9},
            {"substructure_id": "hydroxyl_group", "description": "OH group", "importance_score": 0.4},
            {"substructure_id": "complex_topology", "description": "Bridge structure", "importance_score": 0.1}
        ]
    }

    # Mock Metrics
    metrics = {
        "metadata": {
            "target_type": "logP",
            "is_proxy_target": True
        },
        "gnn_vs_rf": {
            "p_value": 0.03,
            "cohen_d": 0.5
        }
    }

    result = map_feature_ranks(rf_data, gnn_data, metrics)

    # Assertions
    assert "mapping_summary" in result
    assert "unique_gnn_insights" in result
    assert result["mapping_summary"]["total_gnn_substructures"] == 3
    assert result["mapping_summary"]["total_rf_descriptors"] == 3
    assert result["mapping_summary"]["is_proxy_mode"] is True
    assert result["mapping_summary"]["statistical_significance"]["p_value"] == 0.03

    # Check unique insights logic
    # "aromatic_ring" has high GNN score (rank 1). Does it match RF?
    # No direct match in RF features, so it should be a unique insight.
    unique_insights = result["unique_gnn_insights"]
    aromatic_found = False
    for insight in unique_insights:
        if insight["substructure_id"] == "aromatic_ring":
            aromatic_found = True
            assert insight["is_unique_insight"] is True # No match in RF
            assert insight["gnn_rank"] == 1
            break
    
    assert aromatic_found, "Aromatic ring should be identified as a unique insight."

def test_generate_mapping_data_integration():
    """Test the file I/O and end-to-end flow of generate_mapping_data."""
    from analysis.comparative_mapping import generate_mapping_data

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        results_dir = tmpdir / "results"
        results_dir.mkdir()

        # Create mock input files
        rf_file = results_dir / "feature_importance_rf.json"
        with open(rf_file, 'w') as f:
            json.dump({
                "feature_importance": [
                    {"feature": "MW", "mean_abs_shap_value": 0.5}
                ]
            }, f)

        gnn_file = results_dir / "feature_importance_gnn.json"
        with open(gnn_file, 'w') as f:
            json.dump({
                "substructure_importance": [
                    {"substructure_id": "ring", "description": "Ring", "importance_score": 0.9}
                ]
            }, f)

        metrics_file = results_dir / "metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump({
                "metadata": {"target_type": "logP", "is_proxy_target": False},
                "gnn_vs_rf": {"p_value": 0.01, "cohen_d": 0.8}
            }, f)

        # Run the function
        output_path = generate_mapping_data(results_dir, results_dir)

        # Verify output exists and is valid JSON
        assert output_path.exists()
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert "mapping_summary" in data
        assert data["mapping_summary"]["total_gnn_substructures"] == 1
        assert data["mapping_summary"]["total_rf_descriptors"] == 1