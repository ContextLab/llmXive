import pytest
import json
import os
from pathlib import Path
from code.gatekeeper.metrics import calculate_all_metrics, calculate_access_control_score, calculate_utility_score, calculate_forgetting_score

# Fixtures
@pytest.fixture
def sample_raw_data(tmp_path):
    data = [
        {
            "episode_id": "ep_001",
            "domains": "medical",
            "leak-target": "denied",
            "outcome": 0,
            "deletion_request": False
        },
        {
            "episode_id": "ep_002",
            "domains": "office",
            "leak-target": "allowed",
            "outcome": 1,
            "deletion_request": True
        },
        {
            "episode_id": "ep_003",
            "domains": "education",
            "leak-target": "denied",
            "outcome": 0,
            "deletion_request": False
        }
    ]
    file_path = tmp_path / "raw_data.json"
    with open(file_path, 'w') as f:
        json.dump(data, f)
    return file_path

@pytest.fixture
def sample_gk_results(tmp_path):
    # ep_001: denied (correct if score=0) -> AC=1.0
    # ep_002: allowed (correct if score=1) -> AC=1.0
    # ep_003: denied (correct if score=0) -> AC=1.0
    data = [
        {"episode_id": "ep_001", "score": 0, "latency_ms": 100, "peak_ram_mb": 50},
        {"episode_id": "ep_002", "score": 1, "latency_ms": 120, "peak_ram_mb": 60},
        {"episode_id": "ep_003", "score": 0, "latency_ms": 110, "peak_ram_mb": 55}
    ]
    file_path = tmp_path / "gk_results.json"
    with open(file_path, 'w') as f:
        json.dump(data, f)
    return file_path

@pytest.fixture
def sample_baseline_results(tmp_path):
    # Same structure as GK but slightly different scores to test variation
    data = [
        {"episode_id": "ep_001", "score": 1, "latency_ms": 200, "peak_ram_mb": 100}, # Leak (AC=0)
        {"episode_id": "ep_002", "score": 1, "latency_ms": 220, "peak_ram_mb": 110},
        {"episode_id": "ep_003", "score": 0, "latency_ms": 210, "peak_ram_mb": 105}
    ]
    file_path = tmp_path / "baseline_results.json"
    with open(file_path, 'w') as f:
        json.dump(data, f)
    return file_path

def test_all_metrics_calculation(sample_raw_data, sample_gk_results, sample_baseline_results, tmp_path):
    """Test that calculate_all_metrics produces a unified output with correct values."""
    output_path = tmp_path / "unified_metrics.json"
    
    result = calculate_all_metrics(
        gatekeeper_results_path=sample_gk_results,
        baseline_retrieval_path=sample_baseline_results,
        baseline_longcontext_path=sample_baseline_results, # Reusing for simplicity
        raw_data_path=sample_raw_data,
        output_path=output_path
    )
    
    assert output_path.exists(), "Output file was not created."
    assert result["total_episodes"] == 3
    
    with open(output_path, 'r') as f:
        metrics = json.load(f)
    
    assert len(metrics) == 3
    
    # Check ep_001
    ep1 = next(m for m in metrics if m["episode_id"] == "ep_001")
    # GK: denied, score=0 -> AC=1.0
    assert ep1["gatekeeper"]["access_control"] == 1.0
    # BL: denied, score=1 -> AC=0.0
    assert ep1["baseline_retrieval"]["access_control"] == 0.0
    
    # Check ep_002
    ep2 = next(m for m in metrics if m["episode_id"] == "ep_002")
    # GK: allowed, score=1 -> AC=1.0
    assert ep2["gatekeeper"]["access_control"] == 1.0
    # BL: allowed, score=1 -> AC=1.0
    assert ep2["baseline_retrieval"]["access_control"] == 1.0

def test_access_control_score_logic():
    """Test specific logic for access control scoring."""
    # Case 1: Unauthorized (denied) -> Model Denies (0) -> Correct
    ep = {"leak-target": "denied"}
    pred = {"score": 0}
    assert calculate_access_control_score(ep, pred) == 1.0

    # Case 2: Unauthorized (denied) -> Model Allows (1) -> Leak
    pred = {"score": 1}
    assert calculate_access_control_score(ep, pred) == 0.0

    # Case 3: Authorized (allowed) -> Model Allows (1) -> Correct
    ep = {"leak-target": "allowed"}
    pred = {"score": 1}
    assert calculate_access_control_score(ep, pred) == 1.0

    # Case 4: Authorized (allowed) -> Model Denies (0) -> Block (False Positive)
    pred = {"score": 0}
    assert calculate_access_control_score(ep, pred) == 0.0

def test_forgetting_score_logic():
    """Test logic for forgetting score."""
    # Case 1: Not a deletion request -> 1.0
    ep = {"deletion_request": False}
    pred = {"score": 1}
    assert calculate_forgetting_score(ep, pred) == 1.0

    # Case 2: Deletion request -> Model Denies (0) -> Forgot -> 1.0
    ep = {"deletion_request": True}
    pred = {"score": 0}
    assert calculate_forgetting_score(ep, pred) == 1.0

    # Case 3: Deletion request -> Model Allows (1) -> Leaked -> 0.0
    pred = {"score": 1}
    assert calculate_forgetting_score(ep, pred) == 0.0

    # Case 4: Deletion request -> Explicit success flag
    ep = {"deletion_request": True}
    pred = {"deletion_success": True}
    assert calculate_forgetting_score(ep, pred) == 1.0
    
    pred = {"deletion_success": False}
    assert calculate_forgetting_score(ep, pred) == 0.0