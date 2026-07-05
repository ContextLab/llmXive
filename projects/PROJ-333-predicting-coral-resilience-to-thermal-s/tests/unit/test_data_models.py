"""
Unit tests for data models defined in code/data/models.py.
"""

import pytest
from code.data.models import (
    Sample,
    Variant,
    Genotype,
    Phenotype,
    Dataset,
    QualityMetrics,
    GenotypeCall,
    Sex,
)
import pandas as pd


class TestSample:
    def test_create_sample(self):
        sample = Sample(
            sample_id="S001",
            individual_id="I001",
            paternal_id="0",
            maternal_id="0",
            sex=Sex.MALE,
            phenotype=1.0
        )
        assert sample.sample_id == "S001"
        assert sample.individual_id == "I001"
        assert sample.sex == Sex.MALE
        assert sample.phenotype == 1.0

    def test_plink_fam_row(self):
        sample = Sample(
            sample_id="S001",
            individual_id="I001",
            paternal_id="0",
            maternal_id="0",
            sex=Sex.FEMALE,
            phenotype=2.0
        )
        row = sample.to_plink_fam_row()
        assert row == "S001 I001 0 0 2 2.0"

    def test_default_values(self):
        sample = Sample(sample_id="S002", individual_id="I002")
        assert sample.paternal_id == "0"
        assert sample.maternal_id == "0"
        assert sample.sex == Sex.UNKNOWN
        assert sample.phenotype == -9.0


class TestVariant:
    def test_create_variant(self):
        variant = Variant(
            variant_id="rs12345",
            chromosome="1",
            position=100000,
            reference_allele="A",
            alternate_allele="T"
        )
        assert variant.variant_id == "rs12345"
        assert variant.chromosome == "1"
        assert variant.position == 100000
        assert variant.reference_allele == "A"
        assert variant.alternate_allele == "T"

    def test_plink_bim_row(self):
        variant = Variant(
            variant_id="rs12345",
            chromosome="1",
            position=100000,
            reference_allele="A",
            alternate_allele="T"
        )
        row = variant.to_plink_bim_row()
        # Format: chr, variant_id, genetic_pos, bp_pos, allele1, allele2
        assert row == "1 rs12345 0 100000 T A"


class TestGenotype:
    def test_genotype_properties(self):
        g1 = Genotype("rs1", "S1", GenotypeCall.HOMO_REF)
        assert g1.is_homo_ref
        assert not g1.is_het
        assert not g1.is_homo_alt
        assert not g1.is_missing

        g2 = Genotype("rs1", "S1", GenotypeCall.HET)
        assert g2.is_het

        g3 = Genotype("rs1", "S1", GenotypeCall.HOMO_ALT)
        assert g3.is_homo_alt

        g4 = Genotype("rs1", "S1", GenotypeCall.MISSING)
        assert g4.is_missing


class TestPhenotype:
    def test_from_dataframe_row(self):
        data = {
            "sample_id": "S001",
            "survival": 1.0,
            "temp": 30.5
        }
        row = pd.Series(data)
        p = Phenotype.from_dataframe_row(row, "sample_id", "survival")
        assert p.sample_id == "S001"
        assert p.trait_name == "survival"
        assert p.value == 1.0
        assert p.is_binary
        assert "temp" in p.raw_data

    def test_continuous_trait(self):
        data = {
            "sample_id": "S002",
            "growth_rate": 1.5
        }
        row = pd.Series(data)
        p = Phenotype.from_dataframe_row(row, "sample_id", "growth_rate")
        assert p.value == 1.5
        assert not p.is_binary


class TestQualityMetrics:
    def test_retention_rates(self):
        metrics = QualityMetrics(
            total_samples=100,
            retained_samples=80,
            total_variants=1000,
            retained_variants=900
        )
        assert metrics.sample_retention_rate == 0.8
        assert metrics.variant_retention_rate == 0.9

    def test_zero_division_handling(self):
        metrics = QualityMetrics()
        assert metrics.sample_retention_rate == 0.0
        assert metrics.variant_retention_rate == 0.0

    def test_to_dict(self):
        metrics = QualityMetrics(
            total_samples=10,
            retained_samples=5,
            total_variants=100,
            retained_variants=50,
            maf_threshold=0.05,
            missingness_threshold=0.1
        )
        d = metrics.to_dict()
        assert d["total_samples"] == 10
        assert d["retained_samples"] == 5
        assert d["maf_threshold"] == 0.05
        assert d["variant_retention_rate"] == 0.5


class TestDataset:
    def test_dataset_summary(self):
        dataset = Dataset(
            name="TestDataset",
            species="Acropora millepora",
            source="NCBI Test"
        )
        dataset.samples.append(Sample("S1", "I1"))
        dataset.samples.append(Sample("S2", "I2"))
        dataset.variants.append(Variant("rs1", "1", 100, "A", "T"))

        summary = dataset.to_summary()
        assert "TestDataset" in summary
        assert "Acropora millepora" in summary
        assert "Samples: 2" in summary
        assert "Variants: 1" in summary

    def test_maps(self):
        dataset = Dataset(name="Test", species="Test", source="Test")
        s1 = Sample("S1", "I1")
        s2 = Sample("S2", "I2")
        dataset.samples.append(s1)
        dataset.samples.append(s2)

        sample_map = dataset.get_sample_map()
        assert "S1" in sample_map
        assert sample_map["S1"].individual_id == "I1"
        assert "S2" in sample_map