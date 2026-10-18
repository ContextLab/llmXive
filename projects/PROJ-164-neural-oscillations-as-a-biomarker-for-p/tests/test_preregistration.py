"""Tests for T009a: pre-registration draft generation."""
import json
import re

from reports.preregister import (
    ALPHA,
    POWER,
    R2_TARGET,
    compute_analysis_plan_hash,
    generate_pre_registration,
)


def test_analysis_plan_hash_is_sha256():
    h = compute_analysis_plan_hash()
    assert re.fullmatch(r"[0-9a-f]{64}", h) is not None
    # Deterministic
    assert h == compute_analysis_plan_hash()


def test_pre_registration_contents():
    doc = generate_pre_registration()
    assert doc["parameters"]["r2_target"] == R2_TARGET == 0.1
    assert doc["parameters"]["power"] == POWER == 0.8
    assert doc["parameters"]["alpha"] == ALPHA == 0.05
    # Placeholder predictor count before T011
    assert doc["parameters"]["k_predictors"] is None
    assert doc["k_predictors_status"] == "placeholder"
    assert re.fullmatch(r"[0-9a-f]{64}", doc["analysis_plan_hash"])
    # Timestamp is ISO-8601 with timezone
    assert doc["timestamp"].endswith("+00:00")
    # Serializable
    json.dumps(doc)