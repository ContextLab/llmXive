"""
Unit tests for the data models (Participant, Trial).
"""
import pytest
from code.models.data_models import Participant, Trial, StimulusModality, SourceLabel


class TestParticipant:
    def test_create_participant(self):
        p = Participant(participant_id="P001", age=25, gender="F")
        assert p.participant_id == "P001"
        assert p.age == 25
        assert p.gender == "F"
        assert p.get_trial_count() == 0

    def test_add_trial(self):
        p = Participant(participant_id="P001")
        t = Trial(
            trial_id="T1",
            participant_id="P001",
            stimulus_modality=StimulusModality.VISUAL,
            source_label=SourceLabel.REAL,
            participant_response="real",
            confidence_rating=4.0
        )
        p.add_trial(t)
        assert p.get_trial_count() == 1
        assert p.trials[0].trial_id == "T1"

    def test_to_dict(self):
        p = Participant(participant_id="P001", age=30, working_memory=0.85)
        p.add_trial(
            Trial(
                trial_id="T1",
                participant_id="P001",
                stimulus_modality=StimulusModality.AUDITORY,
                source_label=SourceLabel.FABRICATED,
                participant_response="fabricated",
                confidence_rating=3.0
            )
        )
        d = p.to_dict()
        assert d['participant_id'] == "P001"
        assert d['age'] == 30
        assert d['working_memory'] == 0.85
        assert d['trial_count'] == 1


class TestTrial:
    def test_create_trial(self):
        t = Trial(
            trial_id="T1",
            participant_id="P001",
            stimulus_modality=StimulusModality.VISUAL,
            source_label=SourceLabel.REAL,
            participant_response="real",
            confidence_rating=4.0
        )
        assert t.trial_id == "T1"
        assert t.is_correct() is True

    def test_is_correct_mismatch(self):
        t = Trial(
            trial_id="T2",
            participant_id="P001",
            stimulus_modality=StimulusModality.AUDITORY,
            source_label=SourceLabel.REAL,
            participant_response="fabricated",
            confidence_rating=2.0
        )
        assert t.is_correct() is False

    def test_from_row(self):
        row = {
            'trial_id': 'T100',
            'participant_id': 'P99',
            'stimulus_modality': 'visual',
            'source_label': 'fabricated',
            'participant_response': 'fabricated',
            'confidence_rating': 3.5,
            'reaction_time': 1.2
        }
        t = Trial.from_row(row)
        assert t.trial_id == 'T100'
        assert t.participant_id == 'P99'
        assert t.stimulus_modality == StimulusModality.VISUAL
        assert t.source_label == SourceLabel.FABRICATED
        assert t.confidence_rating == 3.5
        assert t.reaction_time == 1.2

    def test_from_row_unknown_modality(self):
        row = {
            'trial_id': 'T101',
            'participant_id': 'P99',
            'stimulus_modality': 'tactile', # Unknown
            'source_label': 'unknown',      # Unknown
            'participant_response': 'test',
            'confidence_rating': 1.0
        }
        t = Trial.from_row(row)
        assert t.stimulus_modality == StimulusModality.UNKNOWN
        assert t.source_label == SourceLabel.UNKNOWN

    def test_to_dict(self):
        t = Trial(
            trial_id="T1",
            participant_id="P001",
            stimulus_modality=StimulusModality.VISUAL,
            source_label=SourceLabel.REAL,
            participant_response="real",
            confidence_rating=4.0,
            reaction_time=0.5
        )
        d = t.to_dict()
        assert d['trial_id'] == "T1"
        assert d['is_correct'] is True
        assert d['reaction_time'] == 0.5
        assert d['stimulus_modality'] == "visual"
        assert d['source_label'] == "real"