import os
import yaml
import numpy as np
import pytest
from pathlib import Path

from code.scoring.sart import score_sart_session, score_sart_trial
from code.scoring.ospan import score_ospan_session
from code.scoring.pss10 import score_pss10
from code.scoring.panas import score_panas

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def load_study_config():
    """
    Load the study configuration YAML file.
    Returns a dict with at least 'seed' and 'pilot_n'.
    """
    config_path = Path('code/config/study_config.yaml')
    if not config_path.is_file():
        raise FileNotFoundError(f"Config file not found at {config_path}")
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# ----------------------------------------------------------------------
# SART tests
# ----------------------------------------------------------------------
def test_sart_commission_and_omission_counts():
    trials = [
        {'stimulus_type': 'non-target', 'response_time': 0.3, 'accuracy': False},  # commission
        {'stimulus_type': 'non-target', 'response_time': 0.4, 'accuracy': True},   # correct non‑target
        {'stimulus_type': 'target',     'response_time': 0.5, 'accuracy': True},   # correct target
        {'stimulus_type': 'target',     'response_time': 0.0, 'accuracy': False},  # omission
    ]
    result = score_sart_session(trials)
    assert result['commission_errors'] == 1
    assert result['omission_errors'] == 1
    # Only the correct target with RT 0.5s is within filter bounds → mean_rt == 0.5
    assert pytest.approx(result['mean_rt'], rel=1e-6) == 0.5

def test_sart_low_attention_flag():
    # 4 target trials, only 1 correct → 25 % accuracy → low_attention True
    trials = []
    for i in range(4):
        trials.append({
            'stimulus_type': 'target',
            'response_time': 0.2 + i * 0.1,
            'accuracy': i == 0  # only first is correct
        })
    result = score_sart_session(trials)
    assert result['low_attention'] is True

def test_sart_rt_filter():
    # Two correct target responses, one below 100 ms, one above 5 s, one valid.
    trials = [
        {'stimulus_type': 'target', 'response_time': 0.05, 'accuracy': True},   # below filter
        {'stimulus_type': 'target', 'response_time': 6.0,  'accuracy': True},   # above filter
        {'stimulus_type': 'target', 'response_time': 1.2,  'accuracy': True},   # valid
    ]
    result = score_sart_session(trials)
    # Only the 1.2 s RT should be counted
    assert pytest.approx(result['mean_rt'], rel=1e-6) == 1.2

# ----------------------------------------------------------------------
# OSPAN tests
# ----------------------------------------------------------------------
def test_ospan_scoring_basic():
    trials = [
        {'stimulus': 'word1', 'recall': 'word1', 'accuracy': True},
        {'stimulus': 'word2', 'recall': 'wrong', 'accuracy': False},
        {'stimulus': 'word3', 'recall': 'word3', 'accuracy': True},
    ]
    result = score_ospan_session(trials)
    assert result['span_score'] == 2
    assert result['total_correct'] == 2

def test_ospan_invalid_input_raises():
    # Missing required key
    trials = [{'stimulus': 'a', 'recall': 'a'}]
    try:
        score_ospan_session(trials)
    except ValueError as e:
        assert 'missing keys' in str(e).lower()
    else:
        assert False, "Expected ValueError for malformed trial"

# ----------------------------------------------------------------------
# PSS‑10 tests
# ----------------------------------------------------------------------
def test_pss10_correct_scoring():
    responses = [0, 1, 2, 3, 4, 0, 1, 2, 3, 4]
    assert score_pss10(responses) == sum(responses)

def test_pss10_invalid_length():
    with pytest.raises(ValueError):
        score_pss10([0, 1, 2])  # too short

def test_pss10_out_of_range():
    responses = [0] * 9 + [5]  # 5 is invalid (max 4)
    with pytest.raises(ValueError):
        score_pss10(responses)

# ----------------------------------------------------------------------
# PANAS tests
# ----------------------------------------------------------------------
def test_panas_correct_scoring():
    # 10 items PA = 1, 10 items NA = 5
    responses = [1] * 10 + [5] * 10
    pa, na = score_panas(responses)
    assert pa == 10   # 10 * 1
    assert na == 50   # 10 * 5

def test_panas_invalid_length():
    with pytest.raises(ValueError):
        score_panas([1] * 19)  # one short

def test_panas_out_of_range():
    responses = [1] * 10 + [6] * 10  # 6 is invalid (>5)
    with pytest.raises(ValueError):
        score_panas(responses)

# ----------------------------------------------------------------------
# Pilot‑check (FR‑009)
# ----------------------------------------------------------------------
def test_pilot_check_scoring_consistency():
    """
    Generates n=pilot_n synthetic participants with trial‑level SART and OSPAN data,
    runs the scoring functions, and asserts that:
      * All SART RTs lie within 100‑5000 ms.
      * The low‑attention flag matches the < 50 % accuracy rule.
      * OSPAN scores equal the sum of the 'accuracy' flags.
    """
    cfg = load_study_config()
    pilot_n = cfg.get('pilot_n', 5)
    seed = cfg.get('seed', 20240521)

    rng = np.random.default_rng(seed)

    # Build synthetic data
    for _ in range(pilot_n):
        # ----- SART -----
        # 30 trials: 20 targets, 10 non‑targets
        sart_trials = []
        target_correct = 0
        for i in range(30):
            is_target = i % 3 != 0  # roughly 2/3 targets
            rt = rng.uniform(0.1, 5.0)  # always within filter bounds
            if is_target:
                # Randomly make 40 % of targets correct to trigger low_attention sometimes
                accuracy = rng.random() < 0.4
                if accuracy:
                    target_correct += 1
            else:
                # 10 % commission errors on non‑targets
                accuracy = rng.random() > 0.9
            sart_trials.append({
                'stimulus_type': 'target' if is_target else 'non-target',
                'response_time': float(rt),
                'accuracy': bool(accuracy)
            })
        sart_result = score_sart_session(sart_trials)

        # Verify RT filter – mean_rt must be within bounds because all RTs are.
        assert 0.1 <= sart_result['mean_rt'] <= 5.0

        # Verify low_attention flag matches the < 50 % rule
        total_targets = sum(1 for t in sart_trials if t['stimulus_type'] == 'target')
        expected_low = (target_correct / total_targets) < 0.5
        assert sart_result['low_attention'] == expected_low

        # ----- OSPAN -----
        # 15 items with random accuracy
        ospan_trials = []
        expected_score = 0
        for i in range(15):
            acc = rng.random() < 0.6
            if acc:
                expected_score += 1
            ospan_trials.append({
                'stimulus': f'word{i}',
                'recall': f'word{i}' if acc else 'wrong',
                'accuracy': bool(acc)
            })
        ospan_result = score_ospan_session(ospan_trials)
        assert ospan_result['span_score'] == expected_score
        assert ospan_result['total_correct'] == expected_score