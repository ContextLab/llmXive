"""
Unit tests for modeling evaluation and interpretation modules.
"""
import os
import sys
import tempfile
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score, roc_auc_score

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.modeling.evaluate import (
    compute_metrics,
    permutation_test,
    compute_correlations_with_fdr,
    sensitivity_analysis,
    generate_learning_curve,
    evaluate_model,
)
from code.modeling.interpret import (
    extract_top_metabolites_shap,
    map_metabolites_to_pathways,
    generate_interpretation_report,
    main as interpret_main,
)
from code.utils.constants import RANDOM_STATE


def test_compute_metrics():
    """Test metrics computation."""
    y_true = np.array([0, 0, 1, 1, 0, 1])
    y_pred = np.array([0, 1, 1, 0, 0, 1])
    y_proba = np.array([0.1, 0.6, 0.7, 0.3, 0.2, 0.8])

    metrics = compute_metrics(y_true, y_pred, y_proba)

    assert "balanced_accuracy" in metrics
    assert "roc_auc" in metrics
    assert "pr_auc" in metrics
    assert isinstance(metrics["balanced_accuracy"], float)
    assert metrics["balanced_accuracy"] >= 0.0 and metrics["balanced_accuracy"] <= 1.0


def test_permutation_test():
    """Test permutation testing."""
    # Create simple data
    X = np.random.randn(100, 5)
    y = np.random.randint(0, 2, 100)
    
    model = RandomForestClassifier(n_estimators=10, random_state=RANDOM_STATE)
    model.fit(X, y)
    
    obs_score, null_dist, p_val = permutation_test(
        model, X, y, n_permutations=100, random_state=RANDOM_STATE
    )
    
    assert obs_score >= 0.0 and obs_score <= 1.0
    assert len(null_dist) == 100
    assert 0.0 <= p_val <= 1.0
    assert all(0.0 <= s <= 1.0 for s in null_dist)


def test_compute_correlations_with_fdr():
    """Test correlation computation with FDR correction."""
    n_samples = 100
    n_features = 10
    
    X = pd.DataFrame(np.random.randn(n_samples, n_features), columns=[f"feat_{i}" for i in range(n_features)])
    y = pd.Series(np.random.randint(0, 2, n_samples))
    
    corr_df, sig_df = compute_correlations_with_fdr(X, y, alpha=0.05)
    
    assert len(corr_df) == n_features
    assert "metabolite" in corr_df.columns
    assert "correlation" in corr_df.columns
    assert "p_value" in corr_df.columns
    assert "fdr_adjusted_p_value" in corr_df.columns
    
    # Check that FDR-adjusted p-values are monotonic when sorted
    sorted_p = corr_df.sort_values("p_value")["fdr_adjusted_p_value"]
    assert all(sorted_p.diff().fillna(0) >= -1e-10)  # Allow small floating point errors


def test_sensitivity_analysis():
    """Test sensitivity analysis."""
    X = np.random.randn(100, 5)
    y = np.random.randint(0, 2, 100)
    
    model = RandomForestClassifier(n_estimators=10, random_state=RANDOM_STATE)
    model.fit(X, y)
    
    results = sensitivity_analysis(model, X, y, cutoffs=[0.01, 0.05])
    
    assert "cutoff_0.01" in results
    assert "cutoff_0.05" in results
    assert "avg_fp_rate" in results["cutoff_0.01"]
    assert "avg_fn_rate" in results["cutoff_0.01"]
    assert 0.0 <= results["cutoff_0.01"]["avg_fp_rate"] <= 1.0
    assert 0.0 <= results["cutoff_0.01"]["avg_fn_rate"] <= 1.0


def test_generate_learning_curve():
    """Test learning curve generation."""
    X = np.random.randn(200, 5)
    y = np.random.randint(0, 2, 200)
    
    model = RandomForestClassifier(n_estimators=10, random_state=RANDOM_STATE)
    
    train_sizes, train_mean, train_std, test_mean, test_std = generate_learning_curve(
        model, X, y, cv_folds=3, n_points=5, random_state=RANDOM_STATE
    )
    
    assert len(train_sizes) == 5
    assert len(train_mean) == 5
    assert len(train_std) == 5
    assert len(test_mean) == 5
    assert len(test_std) == 5
    
    # Check that scores are in valid range
    assert all(0.0 <= s <= 1.0 for s in train_mean)
    assert all(0.0 <= s <= 1.0 for s in test_mean)
    
    # Check that std is non-negative
    assert all(s >= 0.0 for s in train_std)
    assert all(s >= 0.0 for s in test_std)


def test_evaluate_model_integration(tmp_path):
    """Integration test for full evaluation pipeline."""
    # Create mock data
    n_samples = 100
    n_features = 10
    
    X = np.random.randn(n_samples, n_features)
    y = np.random.randint(0, 2, n_samples)
    
    # Create DataFrame
    X_df = pd.DataFrame(X, columns=[f"metabolite_{i}" for i in range(n_features)])
    y_df = pd.DataFrame({"label": y})
    
    # Train a simple model
    model = RandomForestClassifier(n_estimators=10, random_state=RANDOM_STATE)
    model.fit(X, y)
    
    # Save data and model
    model_path = tmp_path / "model.pkl"
    X_path = tmp_path / "matrix.csv"
    y_path = tmp_path / "labels.csv"
    
    import pickle
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    
    X_df.to_csv(X_path)
    y_df.to_csv(y_path)
    
    # Run evaluation
    results = evaluate_model(
        model_path=str(model_path),
        processed_matrix_path=str(X_path),
        labels_path=str(y_path),
        output_dir=str(tmp_path),
    )
    
    # Check results structure
    assert "metrics" in results
    assert "permutation_test" in results
    assert "correlations" in results
    assert "sensitivity_analysis" in results
    assert "learning_curve" in results
    
    # Check metrics
    assert "balanced_accuracy" in results["metrics"]
    assert "roc_auc" in results["metrics"]
    assert "pr_auc" in results["metrics"]
    
    # Check permutation test
    assert "observed_score" in results["permutation_test"]
    assert "p_value" in results["permutation_test"]
    
    # Check files were created
    assert (tmp_path / "metrics.json").exists()
    assert (tmp_path / "null_distribution.npy").exists()
    assert (tmp_path / "metabolite_correlations.csv").exists()
    assert (tmp_path / "learning_curve.png").exists()


def test_extract_top_metabolites_shap():
    """Test SHAP-based top metabolite extraction."""
    # Create mock SHAP values and feature names
    n_samples = 50
    n_features = 10
    
    shap_values = np.random.randn(n_samples, n_features)
    feature_names = [f"metabolite_{i}" for i in range(n_features)]
    
    top_k = 5
    top_metabolites, top_shap_values = extract_top_metabolites_shap(
        shap_values, feature_names, top_k=top_k
    )
    
    assert len(top_metabolites) == top_k
    assert len(top_shap_values) == top_k
    assert all(isinstance(m, str) for m in top_metabolites)
    assert all(isinstance(v, (int, float)) for v in top_shap_values)
    
    # Check that top metabolites are sorted by absolute SHAP value descending
    abs_shap = [abs(v) for v in top_shap_values]
    assert abs_shap == sorted(abs_shap, reverse=True)


def test_map_metabolites_to_pathways():
    """Test pathway mapping logic for metabolites."""
    # Create mock metabolite data with InChIKeys
    metabolite_data = pd.DataFrame({
        "metabolite": ["metabolite_0", "metabolite_1", "metabolite_2"],
        "inchikey": ["TESTKEY0", "TESTKEY1", "TESTKEY2"],
        "shap_importance": [0.5, 0.3, 0.1]
    })
    
    # Mock pathway mapping results
    # In a real scenario, this would query KEGG/MetaCyc
    # Here we test the logic of the mapping function
    pathway_mapping = map_metabolites_to_pathways(metabolite_data, top_n=2)
    
    assert isinstance(pathway_mapping, list)
    assert len(pathway_mapping) <= 2  # Should not exceed top_n
    
    for item in pathway_mapping:
        assert "metabolite" in item
        assert "pathways" in item
        assert "inchikey" in item
        assert isinstance(item["pathways"], list)


def test_generate_interpretation_report(tmp_path):
    """Test interpretation report generation."""
    # Create mock pathway analysis results
    pathway_results = [
        {
            "metabolite": "metabolite_0",
            "inchikey": "TESTKEY0",
            "pathways": ["Plant Defense", "Phenylpropanoid Pathway"]
        },
        {
            "metabolite": "metabolite_1",
            "inchikey": "TESTKEY1",
            "pathways": ["Secondary Metabolism"]
        }
    ]
    
    # Create mock feature importances
    feature_importances = {
        "metabolite_0": 0.5,
        "metabolite_1": 0.3,
        "metabolite_2": 0.2
    }
    
    # Generate report
    report_path = tmp_path / "interpretation_report.json"
    
    generate_interpretation_report(
        pathway_results=pathway_results,
        feature_importances=feature_importances,
        output_path=str(report_path)
    )
    
    # Verify report was created and contains expected content
    assert report_path.exists()
    
    with open(report_path, "r") as f:
        report = json.load(f)
    
    assert "pathway_analysis" in report
    assert "feature_importances" in report
    assert "summary" in report
    assert "biological_plausibility" in report
    
    # Check summary contains associational language (FR-011)
    summary_text = report["summary"].lower()
    assert "association" in summary_text or "related" in summary_text or "linked" in summary_text


def test_interpret_main_integration(tmp_path):
    """Integration test for interpret.py main function."""
    # Create mock SHAP analysis file
    shap_analysis_path = tmp_path / "shap_analysis.json"
    shap_data = {
        "top_metabolites": [
            {"name": "metabolite_0", "shap_value": 0.5, "inchikey": "TESTKEY0"},
            {"name": "metabolite_1", "shap_value": 0.3, "inchikey": "TESTKEY1"},
            {"name": "metabolite_2", "shap_value": 0.2, "inchikey": "TESTKEY2"}
        ],
        "feature_importances": {
            "metabolite_0": 0.5,
            "metabolite_1": 0.3,
            "metabolite_2": 0.2
        }
    }
    
    with open(shap_analysis_path, "w") as f:
        json.dump(shap_data, f)
    
    # Create mock processed matrix for InChIKey lookup
    matrix_path = tmp_path / "matrix.csv"
    matrix_df = pd.DataFrame({
        "metabolite_0": [1.0, 2.0, 3.0],
        "metabolite_1": [4.0, 5.0, 6.0],
        "metabolite_2": [7.0, 8.0, 9.0]
    })
    matrix_df.to_csv(matrix_path, index=False)
    
    # Run main function
    output_dir = tmp_path / "interpretation_output"
    output_dir.mkdir()
    
    interpret_main(
        shap_analysis_path=str(shap_analysis_path),
        processed_matrix_path=str(matrix_path),
        output_dir=str(output_dir),
        top_n=2
    )
    
    # Verify outputs
    assert (output_dir / "pathway_analysis.json").exists()
    assert (output_dir / "interpretation_report.json").exists()
    
    # Verify pathway analysis content
    with open(output_dir / "pathway_analysis.json", "r") as f:
        pathway_results = json.load(f)
    
    assert isinstance(pathway_results, list)
    assert len(pathway_results) <= 2  # Respects top_n
    
    for item in pathway_results:
        assert "metabolite" in item
        assert "pathways" in item
        assert "inchikey" in item