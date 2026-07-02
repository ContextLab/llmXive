"""
Unit tests for the data models defined in code/models/.
"""
import pytest
import numpy as np
from code.models.eeg_dataset import EEGDataset
from code.models.alpha_power import AlphaPowerMetric
from code.models.plv_metric import PLVMetric
from code.models.wm_capacity import WMCapacity


class TestEEGDataset:
    def test_init_with_subject_id(self):
        dataset = EEGDataset(subject_id="sub-01")
        assert dataset.subject_id == "sub-01"
        assert dataset.preprocessing_steps == []

    def test_add_preprocessing_step(self):
        dataset = EEGDataset(subject_id="sub-01")
        dataset.add_preprocessing_step("filtering")
        assert "filtering" in dataset.preprocessing_steps
        assert len(dataset.preprocessing_steps) == 1

    def test_set_behavioral_score(self):
        dataset = EEGDataset(subject_id="sub-01")
        dataset.set_behavioral_score("k_score", 3.5)
        assert dataset.behavioral_scores["k_score"] == 3.5

    def test_validate_missing_subject(self):
        dataset = EEGDataset(subject_id="")
        assert not dataset.validate()

    def test_validate_no_data(self):
        dataset = EEGDataset(subject_id="sub-01")
        assert not dataset.validate()

    def test_validate_with_data(self):
        dataset = EEGDataset(subject_id="sub-01")
        dataset.raw_data = np.random.rand(64, 1000)
        assert dataset.validate()


class TestAlphaPowerMetric:
    def test_init(self):
        metric = AlphaPowerMetric(
            subject_id="sub-01",
            electrode="Fz",
            condition="high_load",
            power_value=10.5
        )
        assert metric.subject_id == "sub-01"
        assert metric.power_value == 10.5

    def test_to_dict(self):
        metric = AlphaPowerMetric(
            subject_id="sub-01",
            electrode="Pz",
            condition="low_load",
            power_value=5.2,
            frequency_band=(8.0, 13.0)
        )
        d = metric.to_dict()
        assert d['subject_id'] == 'sub-01'
        assert d['electrode'] == 'Pz'
        assert d['power_value'] == 5.2
        assert d['frequency_band_low'] == 8.0

    def test_invalid_power_value(self):
        with pytest.raises(ValueError):
            AlphaPowerMetric(
                subject_id="sub-01",
                electrode="Fz",
                condition="high_load",
                power_value="not_a_number"
            )


class TestPLVMetric:
    def test_init(self):
        metric = PLVMetric(
            subject_id="sub-01",
            electrode_1="Fz",
            electrode_2="Pz",
            plv_value=0.85
        )
        assert metric.plv_value == 0.85

    def test_plv_range_warning(self, caplog):
        # PLV outside 0-1 should trigger warning but not error
        metric = PLVMetric(
            subject_id="sub-01",
            electrode_1="Fz",
            electrode_2="Pz",
            plv_value=1.5
        )
        assert metric.plv_value == 1.5
        # Check if warning was logged (implementation detail)
        assert any("outside" in record.message for record in caplog.records)

    def test_to_dict(self):
        metric = PLVMetric(
            subject_id="sub-01",
            electrode_1="F3",
            electrode_2="P3",
            plv_value=0.45,
            condition="delay"
        )
        d = metric.to_dict()
        assert d['electrode_1'] == 'F3'
        assert d['electrode_2'] == 'P3'
        assert d['condition'] == 'delay'


class TestWMCapacity:
    def test_init_with_k_score(self):
        wm = WMCapacity(subject_id="sub-01", k_score=4.0)
        assert wm.k_score == 4.0
        assert wm.d_prime is None

    def test_init_with_d_prime(self):
        wm = WMCapacity(subject_id="sub-01", d_prime=2.5)
        assert wm.d_prime == 2.5

    def test_to_dict(self):
        wm = WMCapacity(
            subject_id="sub-01",
            k_score=3.0,
            accuracy=0.95,
            source="Cowan"
        )
        d = wm.to_dict()
        assert d['k_score'] == 3.0
        assert d['accuracy'] == 0.95
        assert d['source'] == "Cowan"

    def test_missing_metric_warning(self, caplog):
        # Should warn if neither k nor d' is provided
        wm = WMCapacity(subject_id="sub-01")
        assert any("no primary capacity metric" in record.message for record in caplog.records)