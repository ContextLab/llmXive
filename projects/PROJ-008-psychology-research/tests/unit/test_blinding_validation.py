"""
Unit tests for blinding validation logic in cleaner.py
"""
import pytest
from code.data.cleaner import validate_blinding_status, validate_age, validate_asd_diagnosis, validate_outcomes

class TestBlindingValidation:
    """Tests for blinding status validation"""
    
    def test_blinded_rater_true_flag(self):
        """Test extraction when rater_type is 'blinded' and flag is True"""
        study = {
            'rater_type': 'blinded',
            'blinded_assessment_flag': True
        }
        result = validate_blinding_status(study)
        assert result['rater_type'] == 'blinded'
        assert result['blinded_assessment_flag'] is True
    
    def test_unblinded_rater_false_flag(self):
        """Test extraction when rater_type is 'unblinded' and flag is False"""
        study = {
            'rater_type': 'unblinded',
            'blinded_assessment_flag': False
        }
        result = validate_blinding_status(study)
        assert result['rater_type'] == 'unblinded'
        assert result['blinded_assessment_flag'] is False
    
    def test_mixed_rater_type(self):
        """Test extraction when rater_type is 'mixed'"""
        study = {
            'rater_type': 'mixed',
            'blinded_assessment_flag': None
        }
        result = validate_blinding_status(study)
        assert result['rater_type'] == 'mixed'
        assert result['blinded_assessment_flag'] is None
    
    def test_infer_from_flag_only(self):
        """Test inference of rater_type from blinded_assessment_flag"""
        study = {
            'blinded_assessment_flag': True
        }
        result = validate_blinding_status(study)
        assert result['rater_type'] == 'blinded'
        assert result['blinded_assessment_flag'] is True
    
    def test_unknown_rater_type(self):
        """Test handling of unknown rater type"""
        study = {
            'rater_type': 'unknown',
            'blinded_assessment_flag': None
        }
        result = validate_blinding_status(study)
        assert result['rater_type'] == 'unknown'
        assert result['blinded_assessment_flag'] is None
    
    def test_missing_fields(self):
        """Test handling of missing fields"""
        study = {}
        result = validate_blinding_status(study)
        assert result['rater_type'] == 'unknown'
        assert result['blinded_assessment_flag'] is None

class TestAgeValidation:
    """Tests for age range validation"""
    
    def test_valid_age_range(self):
        """Test valid age range 6-12"""
        study = {
            'age_range': {'min': 8, 'max': 12}
        }
        assert validate_age(study) is True
    
    def test_invalid_age_range_high(self):
        """Test invalid age range with max > 12"""
        study = {
            'age_range': {'min': 8, 'max': 15}
        }
        assert validate_age(study) is False
    
    def test_invalid_age_range_low(self):
        """Test invalid age range with min < 6"""
        study = {
            'age_range': {'min': 5, 'max': 10}
        }
        assert validate_age(study) is False
    
    def test_missing_age_range(self):
        """Test missing age range"""
        study = {}
        assert validate_age(study) is False

class TestDiagnosisValidation:
    """Tests for ASD diagnosis validation"""
    
    def test_valid_asd_diagnosis(self):
        """Test valid ASD diagnosis"""
        study = {
            'diagnosis': 'ASD'
        }
        assert validate_asd_diagnosis(study) is True
    
    def test_invalid_diagnosis(self):
        """Test invalid diagnosis"""
        study = {
            'diagnosis': 'ADHD'
        }
        assert validate_asd_diagnosis(study) is False
    
    def test_missing_diagnosis(self):
        """Test missing diagnosis"""
        study = {}
        assert validate_asd_diagnosis(study) is False

class TestOutcomesValidation:
    """Tests for social skill outcomes validation"""
    
    def test_social_skill_phrase(self):
        """Test outcomes containing 'social skill'"""
        study = {
            'outcomes': ['Social skill improvement', 'Other outcome']
        }
        assert validate_outcomes(study) is True
    
    def test_srs_measure(self):
        """Test outcomes containing SRS measure"""
        study = {
            'outcomes': ['SRS-2 scores', 'Other outcome']
        }
        assert validate_outcomes(study) is True
    
    def test_abc_measure(self):
        """Test outcomes containing ABC measure"""
        study = {
            'outcomes': ['ABC irritability subscale', 'Other outcome']
        }
        assert validate_outcomes(study) is True
    
    def test_ssis_measure(self):
        """Test outcomes containing SSIS measure"""
        study = {
            'outcomes': ['SSIS social skills rating', 'Other outcome']
        }
        assert validate_outcomes(study) is True
    
    def test_pep_measure(self):
        """Test outcomes containing PEP measure"""
        study = {
            'outcomes': ['PEP-3 assessment', 'Other outcome']
        }
        assert validate_outcomes(study) is True
    
    def test_no_social_outcomes(self):
        """Test outcomes without social skill measures"""
        study = {
            'outcomes': ['Cognitive score', 'Memory test']
        }
        assert validate_outcomes(study) is False
    
    def test_empty_outcomes(self):
        """Test empty outcomes list"""
        study = {
            'outcomes': []
        }
        assert validate_outcomes(study) is False
    
    def test_missing_outcomes(self):
        """Test missing outcomes field"""
        study = {}
        assert validate_outcomes(study) is False