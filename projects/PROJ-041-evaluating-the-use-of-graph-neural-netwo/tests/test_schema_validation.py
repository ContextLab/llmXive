"""Validate sample JSON documents against the contracts/*.schema.yaml files."""

import hashlib
import sys
from pathlib import Path

import yaml
from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"


def _load_schema(name: str) -> dict:
    with (CONTRACTS / name).open("r") as f:
        return yaml.safe_load(f)


def _ip_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def test_contracts_exist():
    for name in ("dataset.schema.yaml", "graph.schema.yaml"):
        assert (CONTRACTS / name).is_file(), f"missing contract {name}"


def test_sample_netflow_record_validates():
    schema = _load_schema("dataset.schema.yaml")
    record = {
        "src_ip": _ip_hash("192.168.1.1"),
        "dst_ip": _ip_hash("147.32.84.165"),
        "packets": 12,
        "start_time": 1331904000.0,
        "duration": 1.5,
        "bytes": 8192,
        "label": 1,
    }
    Draft7Validator(schema).validate(record)


def test_invalid_netflow_record_rejected():
    schema = _load_schema("dataset.schema.yaml")
    bad = {
        "src_ip": "not-a-hash",
        "dst_ip": _ip_hash("147.32.84.165"),
        "packets": -3,
        "start_time": 1331904000.0,
        "label": 2,
    }
    errors = list(Draft7Validator(schema).iter_errors(bad))
    assert errors, "schema should reject the malformed record"


def test_sample_graph_validates():
    schema = _load_schema("graph.schema.yaml")
    graph = {
        "directed": True,
        "multigraph": False,
        "nodes": [
            {"id": _ip_hash("192.168.1.1"), "is_anomaly": True},
            {"id": _ip_hash("147.32.84.165"), "is_anomaly": False},
        ],
        "edges": [
            {
                "source": _ip_hash("192.168.1.1"),
                "target": _ip_hash("147.32.84.165"),
                "weight": 42,
                "timestamp": 1331904000.0,
            }
        ],
    }
    Draft7Validator(schema).validate(graph)
