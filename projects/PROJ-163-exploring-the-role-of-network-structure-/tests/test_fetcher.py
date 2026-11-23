"""
Unit tests for code.fetcher.
"""
import json
from datetime import datetime, timedelta, timezone
from unittest import mock
import pytest
import yaml
from jsonschema import validate

from code import fetcher

with open("specs/001-exploring-the-role-of-network-structure/contracts/raw_calibration.schema.yaml", "r") as f:
    RAW_SCHEMA = yaml.safe_load(f)

def make_fake_props(fresh=True):
    now = datetime.now(timezone.utc)
    return {
        "timestamp": now.isoformat() if fresh else (now - timedelta(days=31)).isoformat(),
        "qubits": [
            [{"name": "T1", "value": 100e-6}, {"name": "T2", "value": 50e-6}],
            [{"name": "T1", "value": 110e-6}, {"name": "T2", "value": 60e-6}],
        ],
        "gates": [
            {
                "gate": "cx",
                "parameters": [
                    {"name": "gate_error", "value": 0.01},
                    {"name": "readout_error", "value": 0.02},
                ],
            }
        ],
        "coupling_map": [[0, 1]],
    }

def test_validate_freshness():
    fresh = make_fake_props(fresh=True)
    stale = make_fake_props(fresh=False)
    assert fetcher.validate_data_freshness(fresh)[0] is True
    assert fetcher.validate_data_freshness(stale)[0] is False

def test_extract_performance_metrics():
    props = make_fake_props()
    metrics = fetcher.extract_performance_metrics(props, "ibm_falcon_test")
    assert "t1_mean" in metrics
    assert "chip_family" in metrics
    assert metrics["chip_family"] == "Falcon"
    assert metrics["t1_mean"] == 105e-6

def test_schema_conformance():
    props = make_fake_props()
    # Add required fields for schema
    props["device_id"] = "test_dev"
    props["chip_family"] = "Falcon"
    validate(instance=props, schema=RAW_SCHEMA)

def test_no_synthetic_fallback(monkeypatch):
    monkeypatch.delenv("IBMQ_TOKEN", raising=False)
    monkeypatch.delenv("QISKIT_IBM_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="IBMQ token missing"):
        fetcher.main()