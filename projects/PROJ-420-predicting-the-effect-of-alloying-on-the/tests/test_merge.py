"""Tests for the merge module."""

import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

from code.merge import (
    load_json_file,
    normalize_composition,
    are_compositions_equal,
    prefer_measurement_method,
    merge_and_deduplicate,
)
from code.constants import COMPOSITION_TOLERANCE


class TestLoadJsonFile:
    def test_load_list_json(self, tmp_path):
        data = [{"a": 1}, {"a": 2}]
        file_path = tmp_path / "test.json"
        file_path.write_text(json.dumps(data))

        result = load_json_file(str(file_path))
        assert result == data

    def test_load_dict_json_with_data_key(self, tmp_path):
        data = {"data": [{"a": 1}, {"a": 2}]}
        file_path = tmp_path / "test.json"
        file_path.write_text(json.dumps(data))

        result = load_json_file(str(file_path))
        assert result == data["data"]

    def test_load_dict_json_single(self, tmp_path):
        data = {"a": 1}
        file_path = tmp_path / "test.json"
        file_path.write_text(json.dumps(data))

        result = load_json_file(str(file_path))
        assert result == [data]

    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_json_file(str(tmp_path / "nonexistent.json"))


class TestNormalizeComposition:
    def test_normalize_at_percent(self):
        comp = {"Cu": 0.1, "Mg": 0.2, "Al": 0.7}
        result = normalize_composition(comp)
        assert abs(sum(result.values()) - 1.0) < 0.01

    def test_normalize_wt_percent(self):
        # Approximate weights: Cu=63.5, Mg=24.3, Al=27.0
        comp = {"Cu": 10.0, "Mg": 20.0, "Al": 70.0}
        result = normalize_composition(comp)
        # Should convert to atomic fractions
        assert all(0 <= v <= 1 for v in result.values())
        assert abs(sum(result.values()) - 1.0) < 0.01

    def test_empty_composition(self):
        result = normalize_composition({})
        assert result == {}


class TestAreCompositionsEqual:
    def test_equal_compositions(self):
        comp1 = {"Cu": 0.1, "Mg": 0.2}
        comp2 = {"Cu": 0.1, "Mg": 0.2}
        assert are_compositions_equal(comp1, comp2)

    def test_different_compositions(self):
        comp1 = {"Cu": 0.1, "Mg": 0.2}
        comp2 = {"Cu": 0.1, "Mg": 0.3}
        assert not are_compositions_equal(comp1, comp2)

    def test_equal_within_tolerance(self):
        comp1 = {"Cu": 0.1, "Mg": 0.2}
        comp2 = {"Cu": 0.1 + COMPOSITION_TOLERANCE / 2, "Mg": 0.2}
        assert are_compositions_equal(comp1, comp2)

    def test_different_elements(self):
        comp1 = {"Cu": 0.1, "Mg": 0.2}
        comp2 = {"Cu": 0.1, "Si": 0.2}
        assert not are_compositions_equal(comp1, comp2)


class TestPreferMeasurementMethod:
    def test_ultrasonic_wins(self):
        assert prefer_measurement_method("Ultrasonic", "Direct") == 1
        assert prefer_measurement_method("Ultrasonic", "Resonant") == 1

    def test_direct_wins_over_others(self):
        assert prefer_measurement_method("Direct", "Resonant") == 1
        assert prefer_measurement_method("Direct", "Calculated") == 1

    def test_tie(self):
        assert prefer_measurement_method("Resonant", "Resonant") == 0
        assert prefer_measurement_method(None, None) == 0
        assert prefer_measurement_method("Ultrasonic", "Ultrasonic") == 0

    def test_none_handling(self):
        assert prefer_measurement_method(None, "Direct") == -1
        assert prefer_measurement_method("Direct", None) == 1


class TestMergeAndDeduplicate:
    def test_merge_simple(self, tmp_path):
        mp_data = [
            {
                "poisson_ratio": 0.33,
                "young_modulus": 70.0,
                "composition": {"Cu": 0.1, "Mg": 0.2, "Al": 0.7},
                "measurement_method": "Ultrasonic",
                "source": "MP"
            }
        ]
        nist_data = [
            {
                "poisson_ratio": 0.34,
                "young_modulus": 71.0,
                "composition": {"Cu": 0.1, "Mg": 0.2, "Al": 0.7},
                "measurement_method": "Direct",
                "source": "NIST"
            }
        ]

        output_path = tmp_path / "merged.parquet"
        result_df = merge_and_deduplicate(mp_data, nist_data, str(output_path))

        assert len(result_df) == 1
        assert output_path.exists()

    def test_prefer_ultrasonic(self, tmp_path):
        mp_data = [
            {
                "poisson_ratio": 0.33,
                "young_modulus": 70.0,
                "composition": {"Cu": 0.1, "Mg": 0.2, "Al": 0.7},
                "measurement_method": "Resonant",
                "source": "MP"
            }
        ]
        nist_data = [
            {
                "poisson_ratio": 0.34,
                "young_modulus": 70.0,
                "composition": {"Cu": 0.1, "Mg": 0.2, "Al": 0.7},
                "measurement_method": "Ultrasonic",
                "source": "NIST"
            }
        ]

        output_path = tmp_path / "merged.parquet"
        result_df = merge_and_deduplicate(mp_data, nist_data, str(output_path))

        assert len(result_df) == 1
        assert result_df.iloc[0]["measurement_method"] == "Ultrasonic"

    def test_prefer_higher_young_modulus_on_tie(self, tmp_path):
        mp_data = [
            {
                "poisson_ratio": 0.33,
                "young_modulus": 70.0,
                "composition": {"Cu": 0.1, "Mg": 0.2, "Al": 0.7},
                "measurement_method": "Resonant",
                "source": "MP"
            }
        ]
        nist_data = [
            {
                "poisson_ratio": 0.34,
                "young_modulus": 75.0,
                "composition": {"Cu": 0.1, "Mg": 0.2, "Al": 0.7},
                "measurement_method": "Resonant",
                "source": "NIST"
            }
        ]

        output_path = tmp_path / "merged.parquet"
        result_df = merge_and_deduplicate(mp_data, nist_data, str(output_path))

        assert len(result_df) == 1
        assert result_df.iloc[0]["young_modulus"] == 75.0

    def test_empty_input_raises(self, tmp_path):
        with pytest.raises(ValueError):
            merge_and_deduplicate([], [], str(tmp_path / "merged.parquet"))