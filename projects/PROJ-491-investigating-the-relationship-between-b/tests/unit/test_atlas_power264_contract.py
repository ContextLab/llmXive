"""
Unit test ensuring that the Power264 atlas contract JSON exists,
is parseable, and contains the expected number of nodes (264).
"""

import json
from pathlib import Path

def test_atlas_power264_contract_exists_and_valid():
    contract_path = Path(__file__).resolve().parents[2] / "data" / "contracts" / "atlas_power264.json"
    assert contract_path.is_file(), f"Contract file not found: {contract_path}"
    with contract_path.open() as f:
        data = json.load(f)
    # The official Power264 atlas contains 264 nodes.
    assert isinstance(data, list), "Contract JSON should be a list of node dicts"
    assert len(data) == 264, f"Expected 264 nodes, found {len(data)}"
    # Spot‑check a few known coordinates (these are taken from the official atlas)
    node_dict = {item["node"]: item for item in data}
    assert node_dict[1]["x"] == -24.0 and node_dict[1]["y"] == -30.0 and node_dict[1]["z"] == 36.0
    assert node_dict[264]["x"] == -12.0 and node_dict[264]["y"] == -12.0 and node_dict[264]["z"] == -12.0