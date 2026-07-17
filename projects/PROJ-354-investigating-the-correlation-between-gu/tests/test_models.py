"""
Unit tests for the data models (Participant, MicrobiomeProfile, CognitiveScore).
"""
import pytest
import pandas as pd
import numpy as np
from datetime import date
from code.models.participant import Participant
from code.models.microbiome import MicrobiomeProfile
from code.models.cognitive import CognitiveScore

class TestParticipant:
    def test_from_row_valid(self):
        data = {
            "eid": 12345,
            "sex": 1,
            "age": 55.5,
            "bmi": 24.0,
            "ethnicity": "White",
            "age_group": "Middle"
        }
        row = pd.Series(data)
        p = Participant.from_row(row)
        
        assert p.participant_id == 12345
        assert p.sex == 1
        assert p.age == 55.5
        assert p.bmi == 24.0
        assert p.age_group == "Middle"
        assert p.is_valid()

    def test_from_row_missing_optional(self):
        data = {"eid": 67890, "sex": 0}
        row = pd.Series(data)
        p = Participant.from_row(row)
        
        assert p.participant_id == 67890
        assert p.age is None
        assert p.is_valid()

    def test_to_dict(self):
        p = Participant(participant_id=1, sex=1, age=30)
        d = p.to_dict()
        assert d["participant_id"] == 1
        assert d["sex"] == 1
        assert "metadata" in d

class TestMicrobiomeProfile:
    def test_from_row_counts(self):
        data = {
            "eid": 100,
            "Genus_A": 100.0,
            "Genus_B": 50.0,
            "Genus_C": 0.0
        }
        row = pd.Series(data)
        taxon_cols = ["Genus_A", "Genus_B", "Genus_C"]
        
        m = MicrobiomeProfile.from_row(row, taxon_cols)
        
        assert m.participant_id == 100
        assert m.raw_counts["Genus_A"] == 100.0
        assert m.raw_counts["Genus_B"] == 50.0
        assert m.raw_counts["Genus_C"] == 0.0
        assert m.total_reads == 150.0

    def test_add_ilr(self):
        m = MicrobiomeProfile(participant_id=1)
        ilr_data = {"ilr_1": 0.5, "ilr_2": -0.2}
        m.add_ilr(ilr_data)
        
        assert m.ilr_coordinates == ilr_data

    def test_get_ilr_dataframe(self):
        m = MicrobiomeProfile(participant_id=1)
        m.add_ilr({"ilr_1": 1.0, "ilr_2": 2.0})
        df = m.get_ilr_dataframe()
        
        assert isinstance(df, pd.DataFrame)
        assert df.shape[0] == 1
        assert "participant_id" in df.columns
        assert "ilr_1" in df.columns

class TestCognitiveScore:
    def test_from_row_fluid_intelligence(self):
        data = {
            "eid": 200,
            "fluid_intelligence": 12.0,
            "reaction_time": 0.5
        }
        row = pd.Series(data)
        c = CognitiveScore.from_row(row)
        
        assert c.participant_id == 200
        assert c.fluid_intelligence == 12.0
        assert c.reaction_time == 0.5
        assert c.is_valid()

    def test_from_row_missing_scores(self):
        data = {"eid": 201}
        row = pd.Series(data)
        c = CognitiveScore.from_row(row)
        
        assert not c.is_valid()
        assert c.composite_score is None

    def test_composite_calculation(self):
        # Simple average logic in from_row
        data = {
            "eid": 202,
            "fluid_intelligence": 10.0,
            "reasoning": 10.0
        }
        row = pd.Series(data)
        c = CognitiveScore.from_row(row)
        # Assuming simple mean of non-None values
        assert c.composite_score == 10.0