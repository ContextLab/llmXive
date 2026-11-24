"""Unit tests for the FR-006 validation utility (T005)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Make code/ importable regardless of pytest invocation directory
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from utils import validation as V


class TestEegChannels:
    def test_valid_channels_pass(self):
        assert V.validate_eeg_channels(
            ["F3", "F4", "Fz", "P3", "P4", "Pz", "Cz"],
            {"F3", "F4", "Fz", "P3", "P4", "Pz"}) is True

    def test_missing_channel_halts_with_fr006_code(self, capsys):
        with pytest.raises(SystemExit) as exc:
            V.validate_eeg_channels(["Fz", "Cz"], {"Fz", "Pz"})
        assert exc.value.code == V.ERR_FR006_EEG_CHANNELS == 10
        err = capsys.readouterr().err
        assert "FR-006" in err
        assert "Missing required electrode" in err

    def test_missing_channel_message_lists_names(self, capsys):
        with pytest.raises(SystemExit):
            V.validate_eeg_channels(["Fz"], {"F3", "Pz"})
        assert "F3" in capsys.readouterr().err
        assert "Pz" in capsys.readouterr().err


class TestBehavioralMetrics:
    def test_valid_metrics_pass(self):
        assert V.validate_behavioral_metrics(
            {"k_score": 3.2, "d_prime": 2.1}) is True

    def test_missing_behavioral_halts_with_fr006_code(self, capsys):
        with pytest.raises(SystemExit) as exc:
            V.validate_behavioral_metrics({"accuracy": 0.8})
        assert exc.value.code == V.ERR_FR006_BEHAVIORAL == 11
        err = capsys.readouterr().err
        assert "Missing behavioral measures" in err
        assert "k_score" in err and "d_prime" in err

    def test_null_metric_halts(self):
        with pytest.raises(SystemExit) as exc:
            V.validate_behavioral_metrics({"k_score": None,
                                           "d_prime": 1.0})
        assert exc.value.code == V.ERR_FR006_BEHAVIORAL

    def test_nan_metric_halts(self):
        with pytest.raises(SystemExit) as exc:
            V.validate_behavioral_metrics({"k_score": float("nan"),
                                           "d_prime": 1.0})
        assert exc.value.code == V.ERR_FR006_BEHAVIORAL


class TestTrialTimestamps:
    def test_valid_timestamps_pass(self):
        assert V.validate_trial_timestamps([0.0, 1.1, 2.2]) is True

    def test_none_halts_with_fr006_code(self):
        with pytest.raises(SystemExit) as exc:
            V.validate_trial_timestamps(None)
        assert exc.value.code == V.ERR_FR006_TRIAL_TIMESTAMPS == 12

    def test_empty_halts(self):
        with pytest.raises(SystemExit) as exc:
            V.validate_trial_timestamps([])
        assert exc.value.code == V.ERR_FR006_TRIAL_TIMESTAMPS

    def test_non_numeric_halts(self):
        with pytest.raises(SystemExit) as exc:
            V.validate_trial_timestamps(["a", "b"])
        assert exc.value.code == V.ERR_FR006_TRIAL_TIMESTAMPS


class TestDataframeAndCsv:
    def test_empty_dataframe_halts(self):
        with pytest.raises(SystemExit) as exc:
            V.validate_dataframe_not_empty(pd.DataFrame())
        assert exc.value.code == V.ERR_FR006_EMPTY_DATA == 15

    def test_missing_file_halts(self, tmp_path):
        with pytest.raises(SystemExit) as exc:
            V.validate_file_exists(tmp_path / "nope.csv")
        assert exc.value.code == V.ERR_FR006_FILE_NOT_FOUND == 16

    def test_load_and_validate_csv_ok(self, tmp_path):
        p = tmp_path / "m.csv"
        pd.DataFrame({"subject": ["s1"], "k_score": [2.0]}).to_csv(
            p, index=False)
        df = V.load_and_validate_csv(p, ["subject", "k_score"])
        assert list(df.columns) == ["subject", "k_score"]

    def test_load_and_validate_csv_missing_column(self, tmp_path):
        p = tmp_path / "m.csv"
        pd.DataFrame({"subject": ["s1"]}).to_csv(p, index=False)
        with pytest.raises(SystemExit) as exc:
            V.load_and_validate_csv(p, ["subject", "k_score"])
        assert exc.value.code == V.ERR_FR006_MISSING_COLUMNS == 13


class TestDatasetFields:
    def test_missing_fields_halts(self):
        with pytest.raises(SystemExit) as exc:
            V.validate_dataset({"id": "ds000248"},
                               ["id", "participants"])
        assert exc.value.code == V.ERR_FR006_DATASET_FIELDS == 14

    def test_valid_dataset_passes(self):
        assert V.validate_dataset(
            {"id": "ds000248", "participants": 52},
            ["id", "participants"]) is True


class TestExitOnValidationFailure:
    def test_true_condition_continues(self):
        V.exit_on_validation_failure(True, "should not fire")

    def test_false_condition_halts_with_code(self):
        with pytest.raises(SystemExit) as exc:
            V.exit_on_validation_failure(False, "bad",
                                         V.ERR_FR006_BEHAVIORAL)
        assert exc.value.code == V.ERR_FR006_BEHAVIORAL


class TestPowerRequirements:
    def test_insufficient_halts_exit_1(self, tmp_path):
        out = tmp_path / "power_status.json"
        with pytest.raises(SystemExit) as exc:
            V.check_power_requirements(10, out)
        assert exc.value.code == 1

    def test_limited_writes_status(self, tmp_path):
        out = tmp_path / "power_status.json"
        status = V.check_power_requirements(40, out)
        assert status == "LIMITED"
        import json
        data = json.loads(out.read_text())
        assert data["n_count"] == 40
        assert data["status"] == "LIMITED"

    def test_sufficient_ok(self, tmp_path):
        out = tmp_path / "power_status.json"
        assert V.check_power_requirements(60, out) == "OK"


class TestErrorCodeRegistry:
    def test_all_codes_distinct_and_documented(self):
        codes = list(V.ERROR_CODES.values())
        assert len(codes) == len(set(codes))
        for name in ["FR006_EEG_CHANNELS", "FR006_BEHAVIORAL",
                     "FR006_TRIAL_TIMESTAMPS"]:
            assert name in V.ERROR_CODES