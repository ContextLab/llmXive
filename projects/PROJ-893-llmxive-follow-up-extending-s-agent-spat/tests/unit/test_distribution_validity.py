"""Unit tests for T007: distributional validity gate (KS-tests)."""
import json
import sys
from pathlib import Path

import pytest

CODE_DIR = Path(__file__).resolve().parents[2] / "code"
sys.path.insert(0, str(CODE_DIR))

from data.validate_distribution import (
    extract_object_density,
    extract_spatial_variance,
    ks_test_manual,
    perform_ks_test,
    load_derived_data,
)


class TestExtractObjectDensity:
    def test_explicit_field(self):
        scene = {"object_density": 4.5}
        assert extract_object_density(scene) == 4.5

    def test_metadata_field(self):
        scene = {"metadata": {"object_density": 2.0}}
        assert extract_object_density(scene) == 2.0

    def test_count_from_geometry_objects(self):
        scene = {"geometry": {"objects": [{"x": 1}, {"x": 2}, {"x": 3}]}}
        assert extract_object_density(scene) == 3.0

    def test_count_from_flat_objects(self):
        scene = {"objects": [{"id": "a"}, {"id": "b"}]}
        assert extract_object_density(scene) == 2.0

    def test_missing_returns_none(self):
        assert extract_object_density({"foo": "bar"}) is None


class TestExtractSpatialVariance:
    def test_flat_objects_position_lists(self):
        scene = {
            "objects": [
                {"position": [0.0, 0.0, 0.0]},
                {"position": [2.0, 0.0, 0.0]},
            ]
        }
        # 1D along X: variance of [0, 2] = 1.0
        assert extract_spatial_variance(scene) == pytest.approx(1.0)

    def test_2d_spread_from_centroid(self):
        scene = {
            "objects": [
                {"position": [0.0, 0.0, 0.0]},
                {"position": [2.0, 0.0, 0.0]},
                {"position": [0.0, 2.0, 0.0]},
            ]
        }
        # centroid (2/3, 2/3); distances: sqrt(8/9), sqrt(8/9), sqrt(8/9)
        d = (8.0 / 9.0) ** 0.5
        assert extract_spatial_variance(scene) == pytest.approx(0.0)
        # all distances equal -> variance 0

    def test_geometry_nested(self):
        scene = {"geometry": {"objects": [{"x": 1.0, "y": 0.0}, {"x": 3.0, "y": 0.0}]}}
        assert extract_spatial_variance(scene) == pytest.approx(1.0)

    def test_no_objects_returns_none(self):
        assert extract_spatial_variance({"objects": []}) is None
        assert extract_spatial_variance({}) is None


class TestKSTest:
    def test_identical_distributions_high_p(self):
        vals = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
        d, p = ks_test_manual(vals, list(vals))
        assert d == 0.0
        assert p == 1.0

    def test_different_distributions_low_p(self):
        a = [float(i) for i in range(20)]
        b = [100.0 + float(i) for i in range(20)]
        d, p = ks_test_manual(a, b)
        assert d == 1.0
        assert p < 0.05

    def test_perform_ks_test_success(self):
        vals = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        res = perform_ks_test(vals, list(vals), "object_density")
        assert res["status"] == "success"
        assert res["metric"] == "object_density"
        assert res["d_statistic"] == 0.0
        assert res["p_value"] == 1.0

    def test_perform_ks_test_insufficient_data(self):
        res = perform_ks_test([1.0], [1.0, 2.0], "spatial_variance")
        assert res["status"] == "insufficient_data"
        assert res["d_statistic"] is None
        assert res["p_value"] is None


class TestLoadDerivedData:
    def test_loads_jsonl(self, tmp_path):
        p = tmp_path / "scenes.jsonl"
        p.write_text('{"a": 1}\n\n{"b": 2}\n', encoding="utf-8")
        data = load_derived_data(str(p))
        assert data == [{"a": 1}, {"b": 2}]

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_derived_data(str(tmp_path / "nope.jsonl"))


class TestMainEndToEnd:
    def test_main_writes_output(self):
        """Run main() against the real derived constraints on disk and
        verify the declared output artifact is written with the
        required p_value / d_statistic keys."""
        from data.validate_distribution import main
        from config import Config

        constraints = Config.DERIVED_PATH / "constraints.jsonl"
        if not constraints.exists():
            pytest.skip("data/derived/constraints.jsonl not present")

        main()

        out = Config.DATA_RESULTS / "distribution_validity.json"
        assert out.exists()
        with open(out, "r", encoding="utf-8") as f:
            report = json.load(f)
        assert "object_density" in report
        assert "spatial_variance" in report
        assert "gate" in report
        for metric in ("object_density", "spatial_variance"):
            entry = report[metric]
            # p_value and d_statistic must be present for each metric
            assert "p_value" in entry
            assert "d_statistic" in entry