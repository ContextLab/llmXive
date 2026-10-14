"""
Contract test for the quantization configuration generator.

The test ensures that for each model spec defined in ``code.utils.quantize``,
a JSON configuration file exists for each quantization level (fp16, int8, 4bit)
and that the file validates against ``contracts/config.schema.yaml``.
"""

import json
from pathlib import Path

import jsonschema
import pytest

from utils.quantize import main as quantize_main
from llmxive_toolkit import paths

# Load the JSON schema once
schema_path = Path("contracts") / "config.schema.yaml"
with schema_path.open() as f:
    schema = jsonschema.load(f)

@pytest.fixture(scope="module", autouse=True)
def run_quantize():
    """Run the quantizer once before the tests."""
    # Execute the main function; it will write config files.
    exit_code = quantize_main()
    assert exit_code == 0, "Quantization script exited with non‑zero status"

def _config_path(model_name: str, quant: str) -> Path:
    return Path("data") / "configs" / f"{model_name}_{quant}.json"

@pytest.mark.parametrize(
    "model_name,quant",
    [
        ("gpt-neo-125M", "fp16"),
        ("gpt-neo-125M", "int8"),
        ("gpt-neo-125M", "4bit"),
        ("gpt-neo-350M", "fp16"),
        ("gpt-neo-350M", "int8"),
        ("gpt-neo-350M", "4bit"),
        ("gpt-neo-1.3B", "fp16"),
        ("gpt-neo-1.3B", "int8"),
        ("gpt-neo-1.3B", "4bit"),
    ],
)
def test_config_exists_and_valid(model_name: str, quant: str):
    cfg_path = _config_path(model_name, quant)
    assert cfg_path.is_file(), f"Missing config file {cfg_path}"
    with cfg_path.open() as f:
        data = json.load(f)
    # Validate against the JSON schema
    jsonschema.validate(instance=data, schema=schema)

def test_all_configs_created():
    """Ensure that exactly nine configuration files were produced."""
    cfg_dir = Path("data") / "configs"
    configs = list(cfg_dir.glob("*.json"))
    assert len(configs) == 9, f"Expected 9 config files, found {len(configs)}"