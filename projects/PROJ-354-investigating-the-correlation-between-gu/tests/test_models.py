"""
Unit tests for the data models (Participant, MicrobiomeProfile, CognitiveScore).
"""

import pytest
import pandas as pd
import numpy as np
from code.models import Participant, MicrobiomeProfile, CognitiveScore


class TestParticipant:
    """Tests for the Participant entity."""
    
    def test_create_participant(self):
        """Test basic participant creation."""
        p = Participant(
            participant_id=12345,
            age=55.0,
            sex=1,
            bmi=25.5,
            age_group="50-59"
        )
        assert p.participant_id == 12345
        assert p.age == 55.0
        assert p.sex == 1
        assert p.bmi == 25.5
        assert p.age_group == "50-59"
    
    def test_from_row(self):
        """Test creating participant from pandas row."""
        data = {
            "participant_id": 67890,
            "age": 45.0,
            "sex": 0,
            "bmi": 22.0,
            "age_group": "40-49",
            "antibiotic_use_recent": False
        }
        row = pd.Series(data)
        p = Participant.from_row(row)
        
        assert p.participant_id == 67890
        assert p.age == 45.0
        assert p.sex == 0
        assert p.bmi == 22.0
        assert p.age_group == "40-49"
        assert p.antibiotic_use_recent is False
    
    def test_to_dict(self):
        """Test converting participant to dictionary."""
        p = Participant(
            participant_id=11111,
            age=30.0,
            sex=1
        )
        d = p.to_dict()
        
        assert d["participant_id"] == 11111
        assert d["age"] == 30.0
        assert d["sex"] == 1
    
    def test_validation_valid(self):
        """Test validation with valid data."""
        p = Participant(
            participant_id=12345,
            age=50.0,
            sex=1,
            bmi=25.0
        )
        errors = p.validate()
        assert len(errors) == 0
    
    def test_validation_invalid_age(self):
        """Test validation with invalid age."""
        p = Participant(
            participant_id=12345,
            age=150.0,
            sex=1
        )
        errors = p.validate()
        assert any("Invalid age" in e for e in errors)
    
    def test_validation_invalid_sex(self):
        """Test validation with invalid sex code."""
        p = Participant(
            participant_id=12345,
            age=50.0,
            sex=2
        )
        errors = p.validate()
        assert any("Invalid sex code" in e for e in errors)
    
    def test_validation_missing_id(self):
        """Test validation with missing participant_id."""
        p = Participant(participant_id=-1, age=50.0)
        errors = p.validate()
        assert any("participant_id must be a positive integer" in e for e in errors)

class TestMicrobiomeProfile:
    """Tests for the MicrobiomeProfile entity."""
    
    def test_create_profile(self):
        """Test basic profile creation."""
        counts = {"Bacteroides": 1000.0, "Faecalibacterium": 500.0}
        p = MicrobiomeProfile(
            participant_id=12345,
            genus_counts=counts
        )
        assert p.participant_id == 12345
        assert p.genus_counts == counts
    
    def test_from_row(self):
        """Test creating profile from pandas row."""
        data = {
            "participant_id": 67890,
            "genus_Bacteroides": 1000.0,
            "genus_Faecalibacterium": 500.0,
            "total_reads": 15000
        }
        row = pd.Series(data)
        count_cols = ["genus_Bacteroides", "genus_Faecalibacterium"]
        
        p = MicrobiomeProfile.from_row(row, count_cols)
        
        assert p.participant_id == 67890
        assert p.genus_counts["Bacteroides"] == 1000.0
        assert p.genus_counts["Faecalibacterium"] == 500.0
        assert p.total_reads == 15000
    
    def test_get_count_vector(self):
        """Test getting count vector."""
        counts = {"A": 10.0, "B": 20.0, "C": 30.0}
        p = MicrobiomeProfile(participant_id=1, genus_counts=counts)
        vec = p.get_count_vector()
        
        assert len(vec) == 3
        assert np.allclose(sorted(vec), [10.0, 20.0, 30.0])
    
    def test_get_taxa_names(self):
        """Test getting taxa names."""
        counts = {"Bacteroides": 1000.0, "Faecalibacterium": 500.0}
        p = MicrobiomeProfile(participant_id=1, genus_counts=counts)
        names = p.get_taxa_names()
        
        assert set(names) == {"Bacteroides", "Faecalibacterium"}
    
    def test_transformation_flags(self):
        """Test transformation status flags."""
        p = MicrobiomeProfile(participant_id=1)
        
        assert not p.is_zero_replaced()
        assert not p.is_clr_transformed()
        assert not p.is_ilr_transformed()
        
        p.zero_replaced_counts = {"A": 1.0}
        assert p.is_zero_replaced()
        
        p.clr_coordinates = {"A": 0.5}
        assert p.is_clr_transformed()
        
        p.ilr_coordinates = {"ilr_1": 0.2}
        assert p.is_ilr_transformed()
    
    def test_validation_valid(self):
        """Test validation with valid data."""
        p = MicrobiomeProfile(
            participant_id=12345,
            genus_counts={"A": 100.0, "B": 200.0},
            total_reads=1000
        )
        errors = p.validate()
        assert len(errors) == 0
    
    def test_validation_negative_count(self):
        """Test validation with negative count."""
        p = MicrobiomeProfile(
            participant_id=12345,
            genus_counts={"A": -10.0}
        )
        errors = p.validate()
        assert any("Negative count" in e for e in errors)
    
    def test_validation_mismatched_dimensions(self):
        """Test validation with mismatched zero-replaced counts."""
        p = MicrobiomeProfile(
            participant_id=12345,
            genus_counts={"A": 100.0, "B": 200.0},
            zero_replaced_counts={"A": 1.0}  # Missing B
        )
        errors = p.validate()
        assert any("dimension mismatch" in e for e in errors)

class TestCognitiveScore:
    """Tests for the CognitiveScore entity."""
    
    def test_create_score(self):
        """Test basic score creation."""
        s = CognitiveScore(
            participant_id=12345,
            fluid_intelligence_score=10.0,
            reaction_time_ms=500.0
        )
        assert s.participant_id == 12345
        assert s.fluid_intelligence_score == 10.0
        assert s.reaction_time_ms == 500.0
    
    def test_from_row(self):
        """Test creating score from pandas row."""
        data = {
            "participant_id": 67890,
            "fluid_intelligence_score": 8.0,
            "reaction_time_ms": 600.0,
            "assessment_date": "2020-01-15"
        }
        row = pd.Series(data)
        s = CognitiveScore.from_row(row)
        
        assert s.participant_id == 67890
        assert s.fluid_intelligence_score == 8.0
        assert s.reaction_time_ms == 600.0
        assert s.assessment_date == "2020-01-15"
    
    def test_get_primary_score(self):
        """Test getting primary score."""
        s = CognitiveScore(
            participant_id=1,
            fluid_intelligence_score=9.0,
            reaction_time_ms=400.0
        )
        assert s.get_primary_score() == 9.0
    
    def test_get_all_scores(self):
        """Test getting all scores."""
        s = CognitiveScore(
            participant_id=1,
            fluid_intelligence_score=9.0,
            reaction_time_ms=400.0,
            pairs_matching_accuracy=0.85
        )
        scores = s.get_all_scores()
        
        assert scores["fluid_intelligence"] == 9.0
        assert scores["reaction_time"] == 400.0
        assert scores["pairs_matching"] == 0.85
    
    def test_has_valid_primary_score(self):
        """Test checking for valid primary score."""
        s1 = CognitiveScore(participant_id=1, fluid_intelligence_score=9.0)
        assert s1.has_valid_primary_score()
        
        s2 = CognitiveScore(participant_id=1)
        assert not s2.has_valid_primary_score()
    
    def test_validation_valid(self):
        """Test validation with valid data."""
        s = CognitiveScore(
            participant_id=12345,
            fluid_intelligence_score=10.0,
            reaction_time_ms=500.0
        )
        errors = s.validate()
        assert len(errors) == 0
    
    def test_validation_invalid_fluid_intelligence(self):
        """Test validation with out-of-range fluid intelligence."""
        s = CognitiveScore(
            participant_id=12345,
            fluid_intelligence_score=15.0  # > 13
        )
        errors = s.validate()
        assert any("out of range" in e for e in errors)
    
    def test_validation_invalid_reaction_time(self):
        """Test validation with negative reaction time."""
        s = CognitiveScore(
            participant_id=12345,
            reaction_time_ms=-100.0
        )
        errors = s.validate()
        assert any("Reaction time must be positive" in e for e in errors)
    
    def test_validation_missing_id(self):
        """Test validation with missing participant_id."""
        s = CognitiveScore(participant_id=-1, fluid_intelligence_score=10.0)
        errors = s.validate()
        assert any("participant_id must be a positive integer" in e for e in errors)

class TestIntegration:
    """Integration tests for model interactions."""
    
    def test_data_roundtrip(self):
        """Test that models can be serialized and deserialized."""
        p = Participant(participant_id=1, age=50.0, sex=1)
        d = p.to_dict()
        p2 = Participant(participant_id=d["participant_id"], age=d["age"], sex=d["sex"])
        
        assert p.participant_id == p2.participant_id
        assert p.age == p2.age
        assert p.sex == p2.sex
    
    def test_mixed_model_validation(self):
        """Test validation across different model types."""
        p = Participant(participant_id=1, age=50.0)
        m = MicrobiomeProfile(participant_id=1)
        c = CognitiveScore(participant_id=1)
        
        # All should be valid with minimal data
        assert len(p.validate()) == 0
        assert len(m.validate()) == 0
        assert len(c.validate()) == 0