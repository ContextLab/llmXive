"""
Unit tests for SMARTS pattern loading, validation, and binary vector generation.

Covers the public API of src.features.alerts:
- validate_alert_config
- load_and_validate_alerts
- compile_patterns
- generate_alert_vectors
"""
import json
import sys
import tempfile
from pathlib import Path

import pytest
from rdkit import Chem

# Ensure code/ is importable
TESTS_DIR = Path(__file__).resolve().parent
CODE_DIR = TESTS_DIR.parent.parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from src.features.alerts import (
    validate_alert_config,
    load_and_validate_alerts,
    compile_patterns,
    generate_alert_vectors,
)
from src.utils.logger import setup_default_logger

setup_default_logger()

# Paths to the real project artifacts
CODE_ROOT = CODE_DIR
CONFIG_PATH = CODE_ROOT / "config" / "structural_alerts.json"
SCHEMA_PATH = (
    CODE_ROOT
    / "specs"
    / "001-predicting-molecular-toxicity"
    / "contracts"
    / "alerts.schema.yaml"
)

MINIMAL_SCHEMA = {"type": "object"}


def _mol_from_smiles(smiles: str):
    mol = Chem.MolFromSmiles(smiles)
    assert mol is not None, f"Failed to parse SMILES: {smiles}"
    return mol


class TestAlertValidation:
    """Tests for alert configuration validation logic."""

    def test_valid_config(self):
        config = {
            "patterns": [
                {
                    "pattern_id": "TEST_01",
                    "smarts_string": "[Cl]",
                    "weight": 1.0,
                    "source": "Test",
                    "description": "Chlorine",
                }
            ]
        }
        is_valid, errors = validate_alert_config(config, MINIMAL_SCHEMA)
        assert is_valid is True
        assert errors == []

    def test_missing_required_field(self):
        config = {
            "patterns": [
                {"pattern_id": "TEST_01", "weight": 1.0}
                # missing smarts_string
            ]
        }
        is_valid, errors = validate_alert_config(config, MINIMAL_SCHEMA)
        assert is_valid is False
        assert any("smarts_string" in e for e in errors)

    def test_invalid_smarts(self):
        config = {
            "patterns": [
                {
                    "pattern_id": "TEST_01",
                    "smarts_string": "[Cl",  # unclosed bracket
                    "weight": 1.0,
                }
            ]
        }
        is_valid, errors = validate_alert_config(config, MINIMAL_SCHEMA)
        assert is_valid is False
        assert any("Invalid SMARTS" in e for e in errors)

    def test_duplicate_pattern_id(self):
        config = {
            "patterns": [
                {
                    "pattern_id": "TEST_01",
                    "smarts_string": "[Cl]",
                    "weight": 1.0,
                },
                {
                    "pattern_id": "TEST_01",  # duplicate
                    "smarts_string": "[Br]",
                    "weight": 1.0,
                },
            ]
        }
        is_valid, errors = validate_alert_config(config, MINIMAL_SCHEMA)
        assert is_valid is False
        assert any("Duplicate pattern_id" in e for e in errors)

    def test_non_positive_weight(self):
        config = {
            "patterns": [
                {
                    "pattern_id": "TEST_01",
                    "smarts_string": "[Cl]",
                    "weight": -1.0,
                }
            ]
        }
        is_valid, errors = validate_alert_config(config, MINIMAL_SCHEMA)
        assert is_valid is False
        assert any("Weight must be positive" in e for e in errors)

    def test_missing_patterns_key(self):
        is_valid, errors = validate_alert_config({}, MINIMAL_SCHEMA)
        assert is_valid is False
        assert any("patterns" in e for e in errors)

    def test_empty_patterns_list(self):
        is_valid, errors = validate_alert_config({"patterns": []}, MINIMAL_SCHEMA)
        assert is_valid is False
        assert any("empty" in e for e in errors)

class TestCompilePatterns:
    """Tests for SMARTS compilation."""

    def test_compile_valid_patterns(self):
        patterns = [
            {"pattern_id": "CHLORINE", "smarts_string": "[Cl]", "weight": 1.0},
            {"pattern_id": "BROMINE", "smarts_string": "[Br]", "weight": 1.0},
        ]
        compiled = compile_patterns(patterns)
        assert len(compiled) == 2
        assert [pid for pid, _ in compiled] == ["CHLORINE", "BROMINE"]
        for _, mol_pattern in compiled:
            assert mol_pattern is not None

    def test_compile_skips_invalid_smarts(self):
        patterns = [
            {"pattern_id": "BAD", "smarts_string": "[Cl", "weight": 1.0},
            {"pattern_id": "GOOD", "smarts_string": "[Cl]", "weight": 1.0},
        ]
        compiled = compile_patterns(patterns)
        assert [pid for pid, _ in compiled] == ["GOOD"]

class TestAlertVectors:
    """Tests for binary alert vector generation."""

    def test_generate_vectors_basic(self):
        molecules = [_mol_from_smiles(s) for s in ["CCl", "CCBr", "C"]]
        patterns = [
            {"pattern_id": "CHLORINE", "smarts_string": "[Cl]", "weight": 1.0},
            {"pattern_id": "BROMINE", "smarts_string": "[Br]", "weight": 1.0},
        ]
        compiled = compile_patterns(patterns)
        vectors = generate_alert_vectors(molecules, compiled)

        assert len(vectors) == 3
        # Chloromethane
        assert vectors[0]["CHLORINE"] == 1
        assert vectors[0]["BROMINE"] == 0
        # Bromoethane
        assert vectors[1]["CHLORINE"] == 0
        assert vectors[1]["BROMINE"] == 1
        # Methane
        assert vectors[2]["CHLORINE"] == 0
        assert vectors[2]["BROMINE"] == 0
        # SMILES round-trip present
        assert "smiles" in vectors[0]

    def test_generate_vectors_skips_none_molecules(self):
        molecules = [_mol_from_smiles("CCl"), None, _mol_from_smiles("C")]
        patterns = [
            {"pattern_id": "CHLORINE", "smarts_string": "[Cl]", "weight": 1.0}
        ]
        compiled = compile_patterns(patterns)
        vectors = generate_alert_vectors(molecules, compiled)
        assert len(vectors) == 2

    def test_generate_vectors_empty_compiled(self):
        molecules = [_mol_from_smiles("CCl")]
        vectors = generate_alert_vectors(molecules, [])
        assert len(vectors) == 1
        assert vectors[0] == {"smiles": "CCl"}

    def test_binary_values_only(self):
        molecules = [_mol_from_smiles("c1ccc(cc1)[N+](=O)[O-]"), _mol_from_smiles("CCCC")]
        patterns = [
            {
                "pattern_id": "NITRO_AROMATIC_01",
                "smarts_string": "[*;a]([N+](=O)[O-])",
                "weight": 1.5,
            }
        ]
        compiled = compile_patterns(patterns)
        vectors = generate_alert_vectors(molecules, compiled)
        assert vectors[0]["NITRO_AROMATIC_01"] == 1
        assert vectors[1]["NITRO_AROMATIC_01"] == 0
        assert all(
            v in (0, 1) for vec in vectors for k, v in vec.items() if k != "smiles"
        )

class TestLoadAndValidate:
    """Tests for file loading and validation integration."""

    def test_load_valid_files(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(
                {
                    "patterns": [
                        {
                            "pattern_id": "TEST",
                            "smarts_string": "[Cl]",
                            "weight": 1.0,
                            "source": "Test",
                        }
                    ]
                },
                f,
            )
            config_path = Path(f.name)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write("type: object\n")
            schema_path = Path(f.name)

        try:
            config, errors = load_and_validate_alerts(config_path, schema_path)
            assert errors == []
            assert config is not None
            assert len(config["patterns"]) == 1
            assert config["patterns"][0]["pattern_id"] == "TEST"
        finally:
            config_path.unlink()
            schema_path.unlink()

    def test_missing_config_file(self):
        with pytest.raises(FileNotFoundError):
            load_and_validate_alerts(
                Path("/nonexistent/config.json"),
                Path("/nonexistent/schema.yaml"),
            )

    def test_missing_schema_file(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(
                {
                    "patterns": [
                        {
                            "pattern_id": "TEST",
                            "smarts_string": "[Cl]",
                            "weight": 1.0,
                        }
                    ]
                },
                f,
            )
            config_path = Path(f.name)
        try:
            config, errors = load_and_validate_alerts(
                config_path, Path("/nonexistent/schema.yaml")
            )
            assert config is None
            assert any("not found" in e for e in errors)
        finally:
            config_path.unlink()

    def test_invalid_config_json(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write("{not valid json")
            config_path = Path(f.name)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write("type: object\n")
            schema_path = Path(f.name)
        try:
            config, errors = load_and_validate_alerts(config_path, schema_path)
            assert config is None
            assert any("Invalid JSON" in e for e in errors)
        finally:
            config_path.unlink()
            schema_path.unlink()

    def test_invalid_config_fails_validation(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(
                {
                    "patterns": [
                        {
                            "pattern_id": "TEST",
                            "smarts_string": "[Cl",  # invalid
                            "weight": 1.0,
                        }
                    ]
                },
                f,
            )
            config_path = Path(f.name)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write("type: object\n")
            schema_path = Path(f.name)
        try:
            config, errors = load_and_validate_alerts(config_path, schema_path)
            assert config is None
            assert len(errors) > 0
        finally:
            config_path.unlink()
            schema_path.unlink()

class TestProjectArtifacts:
    """Tests against the real project config and schema files."""

    @pytest.mark.skipif(
        not CONFIG_PATH.exists(), reason="structural_alerts.json not present"
    )
    def test_real_config_validates(self):
        config, errors = load_and_validate_alerts(CONFIG_PATH, SCHEMA_PATH)
        assert errors == [], f"Validation errors: {errors}"
        assert config is not None
        # FR-003: at least 10 curated SMARTS patterns
        assert len(config["patterns"]) >= 10
        # Every pattern carries curated metadata
        for p in config["patterns"]:
            assert p["source"]
            assert p["description"]

    @pytest.mark.skipif(
        not CONFIG_PATH.exists(), reason="structural_alerts.json not present"
    )
    def test_real_config_compiles(self):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        compiled = compile_patterns(config["patterns"])
        assert len(compiled) == len(config["patterns"])

    @pytest.mark.skipif(
        not CONFIG_PATH.exists(), reason="structural_alerts.json not present"
    )
    def test_real_config_vectors(self):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        compiled = compile_patterns(config["patterns"])
        # Nitrobenzene should trigger the nitroaromatic alert
        molecules = [_mol_from_smiles("c1ccc(cc1)[N+](=O)[O-]"), _mol_from_smiles("CCCC")]
        vectors = generate_alert_vectors(molecules, compiled)
        assert len(vectors) == 2
        assert vectors[0]["NITRO_AROMATIC_01"] == 1
        assert vectors[1]["NITRO_AROMATIC_01"] == 0
        for vec in vectors:
            for pid, _ in compiled:
                assert vec[pid] in (0, 1)

if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))