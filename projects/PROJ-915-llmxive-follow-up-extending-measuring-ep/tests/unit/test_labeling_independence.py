"""
Unit Test for Labeling Independence (T019a/T026)

This test verifies that the labeling function in code/labeling.py does NOT
accept or use linguistic feature vectors as inputs. It enforces the
principle that adherence labeling must be based solely on semantic similarity
to ground truth facts and safety refusal detection, independent of
linguistic style features (e.g., modal frequency, imperative ratio).

This test is written first (TDD) to define the interface constraints for
T022 (Semantic Scoring) and T023 (Label Logic).
"""

import inspect
import sys
import os
from pathlib import Path

# Add the project root to the path to allow imports from code/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.labeling import (
    compute_semantic_similarities,
    apply_label_logic,
    detect_safety_refusal,
    compute_refusal_semantic_similarity
)
from code.features import extract_features, run_feature_extraction

# List of linguistic feature column names that should NOT be inputs to labeling
LINGUISTIC_FEATURES = [
    'modal_freq',
    'imperative_ratio',
    'citation_density',
    'is_ratio_undefined',
    'ratio_safe_value',
    'sentence_count'
]

def test_labeling_functions_do_not_accept_feature_vectors():
    """
    Verify that the primary labeling functions do not accept linguistic
    feature vectors as arguments.
    """
    # Check compute_semantic_similarities
    sig_sim = inspect.signature(compute_semantic_similarities)
    params_sim = list(sig_sim.parameters.keys())

    # Check apply_label_logic
    sig_label = inspect.signature(apply_label_logic)
    params_label = list(sig_label.parameters.keys())

    # Check detect_safety_refusal
    sig_safe = inspect.signature(detect_safety_refusal)
    params_safe = list(sig_safe.parameters.keys())

    # Assert that none of the linguistic feature names appear in the parameter lists
    # We check for exact matches or substrings that would indicate a feature vector input
    for func_name, params in [
        ("compute_semantic_similarities", params_sim),
        ("apply_label_logic", params_label),
        ("detect_safety_refusal", params_safe)
    ]:
        for feature in LINGUISTIC_FEATURES:
            assert feature not in params, (
                f"Function '{func_name}' should not accept '{feature}' as a parameter. "
                "Labeling must be independent of linguistic features."
            )

        # Also check for generic names that might imply a feature vector
        generic_feature_names = ['features', 'feature_vector', 'linguistic_features', 'style_features']
        for generic in generic_feature_names:
            assert generic not in params, (
                f"Function '{func_name}' should not accept generic feature parameter '{generic}'. "
                "Labeling must be independent of linguistic features."
            )

def test_labeling_logic_uses_only_semantic_inputs():
    """
    Verify that apply_label_logic only uses semantic similarity scores and
    refusal detection flags, not raw text or linguistic features.
    """
    # Inspect the source code of apply_label_logic to ensure it doesn't
    # reference linguistic feature variables
    source = inspect.getsource(apply_label_logic)

    for feature in LINGUISTIC_FEATURES:
        assert feature not in source, (
            f"apply_label_logic source code contains reference to '{feature}'. "
            "Labeling logic must not depend on linguistic features."
        )

    # Verify it relies on semantic similarity variables
    assert 'sim_false' in source or 'similarity' in source, (
        "apply_label_logic should rely on semantic similarity scores."
    )

def test_semantic_scoring_pipeline_excludes_features():
    """
    Verify that the semantic scoring pipeline does not ingest feature data.
    """
    sig_pipeline = inspect.signature(compute_semantic_similarities)
    params = list(sig_pipeline.parameters.keys())

    # Ensure no feature-related parameters are passed to the scoring function
    for feature in LINGUISTIC_FEATURES:
        assert feature not in params, (
            "compute_semantic_similarities should not accept linguistic features."
        )

def test_labeling_interface_compliance():
    """
    TDD Check: Ensure the labeling interface matches the expected signature
    for T022/T023 without feature dependencies.
    """
    # Expected inputs for semantic scoring: model_output, ground_truth_fact
    # Expected inputs for label logic: similarities, refusal_flag

    sig_sim = inspect.signature(compute_semantic_similarities)
    sig_label = inspect.signature(apply_label_logic)

    # Verify compute_semantic_similarities takes text-based inputs
    assert 'response_text' in sig_sim.parameters or 'model_output' in sig_sim.parameters, (
        "compute_semantic_similarities must accept model response text."
    )
    assert 'correct_answer' in sig_sim.parameters or 'ground_truth' in sig_sim.parameters, (
        "compute_semantic_similarities must accept ground truth facts."
    )

    # Verify apply_label_logic takes computed scores
    # (The exact param names might vary, but should not be raw features)
    label_params = list(sig_label.parameters.keys())
    assert len(label_params) > 0, "apply_label_logic must accept similarity scores."

    # Re-verify independence
    for param in label_params:
        assert param not in LINGUISTIC_FEATURES, (
            f"apply_label_logic parameter '{param}' is a linguistic feature."
        )