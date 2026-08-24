"""
Unit tests for data models (Participant, MicrobiomeProfile, CognitiveScore).

Tests cover:
- Dataclass initialization and validation
- Dictionary conversion (to_dict/from_row)
- Age group computation
- Data integrity checks
"""

import pytest
import pandas as pd
import numpy as np
from datetime import date
from code.models.participant import Participant, create_participant_dataframe
from code.models.microbiome import MicrobiomeProfile, create_microbiome_dataframe
from code.models.cognitive import CognitiveScore, create_cognitive_dataframe, compute_composite_score


class TestParticipant:
    """Tests for the Participant data model."""
    
    def test_basic_initialization(self):
        """Test basic participant creation."""
        p = Participant(participant_id="12345", age=55, sex=1)
        assert p.participant_id == "12345"
        assert p.age == 55
        assert p.sex == 1
        assert p.age_group == "Middle"  # 50 <= 55 < 65
    
    def test_age_group_young(self):
        """Test age group computation for young participants."""
        p = Participant(participant_id="12345", age=40, sex=0)
        assert p.age_group == "Young"
    
    def test_age_group_middle(self):
        """Test age group computation for middle-aged participants."""
        p = Participant(participant_id="12345", age=55, sex=1)
        assert p.age_group == "Middle"
    
    def test_age_group_old(self):
        """Test age group computation for older participants."""
        p = Participant(participant_id="12345", age=70, sex=0)
        assert p.age_group == "Old"
    
    def test_invalid_sex(self):
        """Test validation of sex field."""
        with pytest.raises(ValueError):
            Participant(participant_id="12345", age=50, sex=2)
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        p = Participant(
            participant_id="12345",
            age=55,
            sex=1,
            bmi=25.5,
            antibiotic_use_3mo=True
        )
        d = p.to_dict()
        assert d['participant_id'] == "12345"
        assert d['age'] == 55
        assert d['bmi'] == 25.5
        assert d['antibiotic_use_3mo'] is True
        assert 'age_group' in d
    
    def test_from_row(self):
        """Test creation from pandas Series."""
        data = {
            'eid': '12345',
            'age': 55,
            'sex': 1,
            'bmi': 25.5,
            'antibiotic_use_3mo': True
        }
        row = pd.Series(data)
        p = Participant.from_row(row)
        assert p.participant_id == "12345"
        assert p.age == 55
        assert p.sex == 1
    
    def test_from_dataframe(self):
        """Test creation from DataFrame."""
        df = pd.DataFrame([
            {'eid': '12345', 'age': 55, 'sex': 1},
            {'eid': '12346', 'age': 45, 'sex': 0}
        ])
        participants = Participant.from_dataframe(df)
        assert len(participants) == 2
        assert participants[0].age == 55
        assert participants[1].age == 45
    
    def test_chronic_conditions(self):
        """Test chronic conditions handling."""
        p = Participant(
            participant_id="12345",
            age=55,
            sex=1,
            chronic_conditions=["I10", "E11"]
        )
        assert len(p.chronic_conditions) == 2
        assert "I10" in p.chronic_conditions
    
    def test_to_dataframe(self):
        """Test conversion to DataFrame."""
        p1 = Participant(participant_id="12345", age=55, sex=1)
        p2 = Participant(participant_id="12346", age=45, sex=0)
        df = create_participant_dataframe([p1, p2])
        assert len(df) == 2
        assert list(df['participant_id']) == ["12345", "12346"]


class TestMicrobiomeProfile:
    """Tests for the MicrobiomeProfile data model."""
    
    def test_basic_initialization(self):
        """Test basic microbiome profile creation."""
        abundances = {"Bacteroides": 0.4, "Firmicutes": 0.3, "Actinobacteria": 0.05}
        m = MicrobiomeProfile(
            participant_id="12345",
            sample_id="S001",
            abundances=abundances
        )
        assert m.participant_id == "12345"
        assert m.sample_id == "S001"
        assert m.taxonomy_level == "genus"
    
    def test_get_taxa(self):
        """Test retrieval of taxon names."""
        abundances = {"Bacteroides": 0.4, "Firmicutes": 0.3}
        m = MicrobiomeProfile(
            participant_id="12345",
            sample_id="S001",
            abundances=abundances
        )
        taxa = m.get_taxa()
        assert "Bacteroides" in taxa
        assert "Firmicutes" in taxa
        assert len(taxa) == 2
    
    def test_get_abundances_array(self):
        """Test retrieval of abundances as array."""
        abundances = {"Bacteroides": 0.4, "Firmicutes": 0.3, "Actinobacteria": 0.05}
        m = MicrobiomeProfile(
            participant_id="12345",
            sample_id="S001",
            abundances=abundances
        )
        arr = m.get_abundances_array()
        assert isinstance(arr, np.ndarray)
        assert len(arr) == 3
        # Check sorted order
        expected_order = sorted(abundances.keys())
        assert m.get_taxa() == expected_order
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        abundances = {"Bacteroides": 0.4}
        m = MicrobiomeProfile(
            participant_id="12345",
            sample_id="S001",
            abundances=abundances,
            zero_replaced=True
        )
        d = m.to_dict()
        assert d['participant_id'] == "12345"
        assert d['zero_replaced'] is True
        assert 'abundances' in d
    
    def test_from_row(self):
        """Test creation from pandas Series."""
        data = {
            'eid': '12345',
            'sample_id': 'S001',
            'abundances': '{"Bacteroides": 0.4, "Firmicutes": 0.3}'
        }
        row = pd.Series(data)
        m = MicrobiomeProfile.from_row(row)
        assert m.participant_id == "12345"
        assert m.sample_id == "S001"
        assert "Bacteroides" in m.abundances
    
    def test_from_dataframe(self):
        """Test creation from DataFrame."""
        df = pd.DataFrame([
            {
                'eid': '12345',
                'sample_id': 'S001',
                'abundances': '{"Bacteroides": 0.4}'
            },
            {
                'eid': '12346',
                'sample_id': 'S002',
                'abundances': '{"Firmicutes": 0.5}'
            }
        ])
        profiles = MicrobiomeProfile.from_dataframe(df)
        assert len(profiles) == 2
        assert profiles[0].abundances["Bacteroides"] == 0.4
    
    def test_to_dataframe(self):
        """Test conversion to DataFrame."""
        m1 = MicrobiomeProfile(
            participant_id="12345",
            sample_id="S001",
            abundances={"Bacteroides": 0.4}
        )
        m2 = MicrobiomeProfile(
            participant_id="12346",
            sample_id="S002",
            abundances={"Firmicutes": 0.5}
        )
        df = create_microbiome_dataframe([m1, m2])
        assert len(df) == 2
        assert list(df['participant_id']) == ["12345", "12346"]
        # Check flattened abundance columns
        assert 'abundance_Bacteroides' in df.columns
        assert 'abundance_Firmicutes' in df.columns


class TestCognitiveScore:
    """Tests for the CognitiveScore data model."""
    
    def test_basic_initialization(self):
        """Test basic cognitive score creation."""
        c = CognitiveScore(
            participant_id="12345",
            assessment_id="A001",
            test_type="fluid_intelligence",
            raw_score=12
        )
        assert c.participant_id == "12345"
        assert c.assessment_id == "A001"
        assert c.test_type == "fluid_intelligence"
    
    def test_accuracy_calculation(self):
        """Test automatic accuracy calculation."""
        c = CognitiveScore(
            participant_id="12345",
            assessment_id="A001",
            num_trials=10,
            num_correct=8
        )
        assert c.accuracy == 0.8
    
    def test_accuracy_override(self):
        """Test that provided accuracy is used if present."""
        c = CognitiveScore(
            participant_id="12345",
            assessment_id="A001",
            num_trials=10,
            num_correct=8,
            accuracy=0.9  # Different from calculated
        )
        # Should use provided value (with tolerance check in post_init)
        # The model logs a warning but keeps the provided value
        assert c.accuracy == 0.9
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        c = CognitiveScore(
            participant_id="12345",
            assessment_id="A001",
            test_type="fluid_intelligence",
            raw_score=12,
            scaled_score=100
        )
        d = c.to_dict()
        assert d['participant_id'] == "12345"
        assert d['scaled_score'] == 100
        assert d['test_type'] == "fluid_intelligence"
    
    def test_from_row(self):
        """Test creation from pandas Series."""
        data = {
            'eid': '12345',
            'field_id': 'A001',
            'test_type': 'reaction_time',
            'raw_score': 500,
            'num_trials': 20,
            'num_correct': 18
        }
        row = pd.Series(data)
        c = CognitiveScore.from_row(row)
        assert c.participant_id == "12345"
        assert c.assessment_id == "A001"
        assert c.test_type == "reaction_time"
        assert c.accuracy == 0.9
    
    def test_from_dataframe(self):
        """Test creation from DataFrame."""
        df = pd.DataFrame([
            {
                'eid': '12345',
                'field_id': 'A001',
                'test_type': 'fluid_intelligence',
                'raw_score': 12
            },
            {
                'eid': '12346',
                'field_id': 'A002',
                'test_type': 'reaction_time',
                'raw_score': 500
            }
        ])
        scores = CognitiveScore.from_dataframe(df)
        assert len(scores) == 2
        assert scores[0].test_type == "fluid_intelligence"
    
    def test_to_dataframe(self):
        """Test conversion to DataFrame."""
        c1 = CognitiveScore(
            participant_id="12345",
            assessment_id="A001",
            test_type="fluid_intelligence",
            raw_score=12
        )
        c2 = CognitiveScore(
            participant_id="12346",
            assessment_id="A002",
            test_type="reaction_time",
            raw_score=500
        )
        df = create_cognitive_dataframe([c1, c2])
        assert len(df) == 2
        assert list(df['participant_id']) == ["12345", "12346"]
    
    def test_composite_score(self):
        """Test composite score computation."""
        scores = [
            CognitiveScore(
                participant_id="12345",
                assessment_id="A001",
                test_type="fluid_intelligence",
                scaled_score=100
            ),
            CognitiveScore(
                participant_id="12345",
                assessment_id="A002",
                test_type="reaction_time",
                scaled_score=110
            ),
            CognitiveScore(
                participant_id="12346",
                assessment_id="A003",
                test_type="fluid_intelligence",
                scaled_score=95
            )
        ]
        composites = compute_composite_score(scores)
        assert "12345" in composites
        assert composites["12345"] == 105.0  # Average of 100 and 110
        assert "12346" in composites
        assert composites["12346"] == 95.0
    
    def test_composite_missing_scaled(self):
        """Test composite score when some scores lack scaled values."""
        scores = [
            CognitiveScore(
                participant_id="12345",
                assessment_id="A001",
                test_type="fluid_intelligence",
                raw_score=12  # No scaled_score
            ),
            CognitiveScore(
                participant_id="12345",
                assessment_id="A002",
                test_type="reaction_time",
                scaled_score=110
            )
        ]
        composites = compute_composite_score(scores)
        assert "12345" in composites
        assert composites["12345"] == 110.0  # Only the valid score