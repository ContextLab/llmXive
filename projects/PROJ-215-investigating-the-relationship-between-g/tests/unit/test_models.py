"""
Unit tests for code/models.py data structures.
"""
import pytest
from code.models import MicrobiomeSample, MentalHealthRecord, AssociationResult
import numpy as np


class TestMicrobiomeSample:
    def test_valid_sample_creation(self):
        sample = MicrobiomeSample(
            sample_id="S12345",
            counts={"Bacteroides": 100, "Firmicutes": 200},
            metadata={"sequencing_depth": 5000}
        )
        assert sample.sample_id == "S12345"
        assert sample.metadata["sequencing_depth"] == 5000

    def test_empty_sample_id_raises(self):
        with pytest.raises(ValueError):
            MicrobiomeSample(sample_id="", counts={"a": 1})

    def test_none_counts_raises(self):
        with pytest.raises(ValueError):
            MicrobiomeSample(sample_id="S1", counts=None)


class TestMentalHealthRecord:
    def test_complete_record(self):
        record = MentalHealthRecord(
            phq9=12.0,
            gad7=8.0,
            age=45.0,
            bmi=24.5,
            subject_id="P001"
        )
        assert record.has_missing_key_values() is False
        assert record.is_high_depression() is True  # >= 10
        assert record.is_high_anxiety() is False    # < 10

    def test_missing_values(self):
        record = MentalHealthRecord(phq9=5.0, gad7=None, age=30.0, bmi=22.0)
        assert record.has_missing_key_values() is True
        assert record.is_high_anxiety() is False  # Should not crash on None

    def test_boundary_conditions(self):
        # Exactly 10
        record = MentalHealthRecord(phq9=10.0, gad7=10.0, age=30.0, bmi=22.0)
        assert record.is_high_depression() is True
        assert record.is_high_anxiety() is True

        # Just below 10
        record = MentalHealthRecord(phq9=9.9, gad7=9.9, age=30.0, bmi=22.0)
        assert record.is_high_depression() is False
        assert record.is_high_anxiety() is False


class TestAssociationResult:
    def test_positive_direction(self):
        res = AssociationResult(
            taxon="Bacteroides",
            coef=0.45,
            pval=0.01,
            qval=0.04,
            direction=""  # Should be auto-calculated
        )
        assert res.direction == "positive"
        assert res.is_significant() is True

    def test_negative_direction(self):
        res = AssociationResult(
            taxon="Faecalibacterium",
            coef=-0.30,
            pval=0.02,
            qval=0.06,
            direction=""
        )
        assert res.direction == "negative"
        assert res.is_significant() is False

    def test_zero_coef(self):
        res = AssociationResult(
            taxon="Unknown",
            coef=0.0,
            pval=0.99,
            qval=0.99,
            direction=""
        )
        assert res.direction == "neutral"
        assert res.is_significant() is False