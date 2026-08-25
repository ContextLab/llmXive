"""
Unit tests for the data models (Participant, MicrobiomeProfile, CognitiveScore).
"""
import pytest
import pandas as pd
from datetime import date
from code.models.participant import Participant, create_participant_dataframe
from code.models.microbiome import MicrobiomeProfile, create_microbiome_dataframe
from code.models.cognitive import CognitiveScore, create_cognitive_dataframe, compute_composite_score


class TestParticipant:
    def test_create_participant(self):
        p = Participant(
            participant_id=12345,
            sex=1,
            age=55.0,
            bmi=24.5,
            ethnicity="White",
            assessment_date=date(2023, 1, 15)
        )
        assert p.participant_id == 12345
        assert p.sex == 1
        assert p.age == 55.0

    def test_to_dict(self):
        p = Participant(participant_id=1, sex=0, age=30.0)
        d = p.to_dict()
        assert d["participant_id"] == 1
        assert d["sex"] == 0
        assert "assessment_date" in d

    def test_create_dataframe(self):
        p1 = Participant(participant_id=1, sex=0, age=30.0)
        p2 = Participant(participant_id=2, sex=1, age=40.0)
        df = create_participant_dataframe([p1, p2])
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "participant_id" in df.columns
        assert df["sex"].iloc[0] == 0


class TestMicrobiomeProfile:
    def test_create_profile(self):
        m = MicrobiomeProfile(
            participant_id=123,
            sample_id="S001",
            raw_counts={"Bacteroides": 100, "Firmicutes": 500}
        )
        assert m.participant_id == 123
        assert m.raw_counts["Bacteroides"] == 100

    def test_to_dict_flattens_counts(self):
        m = MicrobiomeProfile(
            participant_id=1,
            sample_id="S1",
            raw_counts={"TaxA": 10, "TaxB": 20}
        )
        d = m.to_dict()
        assert "count_TaxA" in d
        assert d["count_TaxA"] == 10

    def test_create_dataframe(self):
        m1 = MicrobiomeProfile(participant_id=1, sample_id="S1", raw_counts={"A": 10})
        m2 = MicrobiomeProfile(participant_id=2, sample_id="S2", raw_counts={"A": 20, "B": 30})
        df = create_microbiome_dataframe([m1, m2])
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "count_A" in df.columns
        assert df["count_A"].iloc[0] == 10
        assert df["count_B"].iloc[0] == 0.0  # Missing becomes 0 or NaN, handled by fillna


class TestCognitiveScore:
    def test_create_score(self):
        c = CognitiveScore(
            participant_id=999,
            assessment_date=date(2023, 5, 1),
            numeric_memory=85.0,
            reasoning=90.0
        )
        assert c.participant_id == 999
        assert c.numeric_memory == 85.0

    def test_to_dict(self):
        c = CognitiveScore(participant_id=1, numeric_memory=100.0)
        d = c.to_dict()
        assert d["participant_id"] == 1
        assert d["numeric_memory"] == 100.0

    def test_create_dataframe(self):
        c1 = CognitiveScore(participant_id=1, numeric_memory=50.0, reasoning=60.0)
        c2 = CognitiveScore(participant_id=2, numeric_memory=70.0, reasoning=80.0)
        df = create_cognitive_dataframe([c1, c2])
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "numeric_memory" in df.columns

    def test_compute_composite_score(self):
        data = {
            "numeric_memory": [10.0, 20.0, 30.0],
            "reasoning": [10.0, 20.0, 30.0]
        }
        df = pd.DataFrame(data)
        composite = compute_composite_score(df)
        assert isinstance(composite, pd.Series)
        assert len(composite) == 3
        # Check that the mean is approximately 0 due to z-scoring
        assert abs(composite.mean()) < 1e-6