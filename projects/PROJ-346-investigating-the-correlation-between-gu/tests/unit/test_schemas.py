"""
Unit tests for data schema validation in code/schemas.py.

Tests the Pydantic models and validation functions for MicrobialTaxa and CognitiveScore.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from pydantic import ValidationError
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from schemas import MicrobialTaxa, CognitiveScore, validate_microbial_data, validate_cognitive_data

class TestMicrobialTaxa:
    def test_valid_microbial_taxa(self):
        """Test creation of valid MicrobialTaxa instance."""
        data = {
            'sample_id': 'S001',
            'taxa_id': 'ASV_12345',
            'abundance': 0.05,
            'read_count': 5000,
            'phylum': 'Firmicutes',
            'class_': 'Clostridia',
            'order': 'Clostridiales',
            'family': 'Lachnospiraceae',
            'genus': 'Faecalibacterium',
            'species': 'prausnitzii',
            'study_id': 'Qiita_10313',
            'sequencing_date': datetime(2020, 5, 15)
        }
        instance = MicrobialTaxa(**data)
        assert instance.sample_id == 'S001'
        assert instance.abundance == 0.05
        assert instance.taxa_id == 'ASV_12345'

    def test_negative_abundance_raises_error(self):
        """Test that negative abundance raises ValidationError."""
        with pytest.raises(ValidationError):
            MicrobialTaxa(
                sample_id='S001',
                taxa_id='ASV_12345',
                abundance=-0.1,
                read_count=5000,
                study_id='Qiita_10313'
            )

    def test_abundance_greater_than_one_raises_error(self):
        """Test that abundance > 1 raises ValidationError."""
        with pytest.raises(ValidationError):
            MicrobialTaxa(
                sample_id='S001',
                taxa_id='ASV_12345',
                abundance=1.5,
                read_count=5000,
                study_id='Qiita_10313'
            )

    def test_invalid_sample_id_format(self):
        """Test that invalid sample_id format raises ValidationError."""
        with pytest.raises(ValidationError):
            MicrobialTaxa(
                sample_id='S@001',  # Invalid character
                taxa_id='ASV_12345',
                abundance=0.05,
                read_count=5000,
                study_id='Qiita_10313'
            )

    def test_missing_required_field(self):
        """Test that missing required field raises ValidationError."""
        with pytest.raises(ValidationError):
            MicrobialTaxa(
                sample_id='S001',
                taxa_id='ASV_12345',
                abundance=0.05,
                # Missing read_count
                study_id='Qiita_10313'
            )

class TestCognitiveScore:
    def test_valid_cognitive_score(self):
        """Test creation of valid CognitiveScore instance."""
        data = {
            'subject_id': 'SUBJ_001',
            'score_type': 'N-Back',
            'raw_score': 85.5,
            'z_score': 1.2,
            'age': 45,
            'sex': 'M',
            'bmi': 24.5,
            'study_id': 'UKB_20002',
            'assessment_date': datetime(2019, 8, 20)
        }
        instance = CognitiveScore(**data)
        assert instance.subject_id == 'SUBJ_001'
        assert instance.score_type == 'N-Back'
        assert instance.raw_score == 85.5

    def test_invalid_score_type_raises_error(self):
        """Test that invalid score_type raises ValidationError."""
        with pytest.raises(ValidationError):
            CognitiveScore(
                subject_id='SUBJ_001',
                score_type='InvalidTest',
                raw_score=85.5,
                age=45,
                sex='M',
                study_id='UKB_20002'
            )

    def test_invalid_sex_raises_error(self):
        """Test that invalid sex raises ValidationError."""
        with pytest.raises(ValidationError):
            CognitiveScore(
                subject_id='SUBJ_001',
                score_type='N-Back',
                raw_score=85.5,
                age=45,
                sex='X',
                study_id='UKB_20002'
            )

    def test_z_score_out_of_range(self):
        """Test that z_score outside -10 to 10 raises ValidationError."""
        with pytest.raises(ValidationError):
            CognitiveScore(
                subject_id='SUBJ_001',
                score_type='N-Back',
                raw_score=85.5,
                z_score=15.0,
                age=45,
                sex='M',
                study_id='UKB_20002'
            )

    def test_negative_raw_score_raises_error(self):
        """Test that negative raw_score raises ValidationError."""
        with pytest.raises(ValidationError):
            CognitiveScore(
                subject_id='SUBJ_001',
                score_type='N-Back',
                raw_score=-10.0,
                age=45,
                sex='M',
                study_id='UKB_20002'
            )

class TestValidationFunctions:
    def test_validate_microbial_data_valid(self):
        """Test validation function with valid DataFrame."""
        df = pd.DataFrame({
            'sample_id': ['S001', 'S002'],
            'taxa_id': ['ASV_1', 'ASV_2'],
            'abundance': [0.05, 0.1],
            'read_count': [5000, 6000],
            'study_id': ['Qiita_10313', 'Qiita_10313']
        })
        assert validate_microbial_data(df) is True

    def test_validate_microbial_data_missing_column(self):
        """Test validation function with missing column."""
        df = pd.DataFrame({
            'sample_id': ['S001', 'S002'],
            'taxa_id': ['ASV_1', 'ASV_2'],
            'abundance': [0.05, 0.1],
            # Missing read_count and study_id
        })
        with pytest.raises(ValueError, match="Missing required column"):
            validate_microbial_data(df)

    def test_validate_cognitive_data_valid(self):
        """Test validation function with valid DataFrame."""
        df = pd.DataFrame({
            'subject_id': ['SUBJ_001', 'SUBJ_002'],
            'score_type': ['N-Back', 'Task Switching'],
            'raw_score': [85.5, 90.0],
            'age': [45, 50],
            'sex': ['M', 'F'],
            'study_id': ['UKB_20002', 'UKB_20002']
        })
        assert validate_cognitive_data(df) is True

    def test_validate_cognitive_data_missing_column(self):
        """Test validation function with missing column."""
        df = pd.DataFrame({
            'subject_id': ['SUBJ_001', 'SUBJ_002'],
            'score_type': ['N-Back', 'Task Switching'],
            'raw_score': [85.5, 90.0],
            # Missing age, sex, study_id
        })
        with pytest.raises(ValueError, match="Missing required column"):
            validate_cognitive_data(df)
