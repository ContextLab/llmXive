"""
Unit tests for code/data/models.py
"""
import pytest
from pathlib import Path
import json
import tempfile
import os

# Import the module under test
from code.data.models import (
    Trial,
    Participant,
    Stimulus,
    StimulusType,
    save_trials_to_json,
    load_trials_from_json,
    save_stimuli_to_json,
    load_stimuli_from_json
)


class TestStimulus:
    def test_stimulus_creation(self):
        """Test basic instantiation of Stimulus."""
        s = Stimulus(
            stimulus_id="prime_001",
            stimulus_type=StimulusType.PRIME,
            file_path="data/primes/prime_001.png"
        )
        assert s.stimulus_id == "prime_001"
        assert s.stimulus_type == StimulusType.PRIME
        assert s.valence is None
        assert s.ambiguity is None

    def test_stimulus_with_metadata(self):
        """Test Stimulus with optional fields populated."""
        s = Stimulus(
            stimulus_id="target_001",
            stimulus_type=StimulusType.TARGET,
            file_path="data/targets/target_001.png",
            valence=0.8,
            ambiguity=0.2,
            metadata={"source": "OSF"}
        )
        assert s.valence == 0.8
        assert s.ambiguity == 0.2
        assert s.metadata["source"] == "OSF"

    def test_stimulus_to_dict(self):
        """Test serialization of Stimulus."""
        s = Stimulus(
            stimulus_id="prime_001",
            stimulus_type=StimulusType.PRIME,
            file_path="data/primes/prime_001.png",
            valence=-0.5
        )
        d = s.to_dict()
        assert d["stimulus_id"] == "prime_001"
        assert d["stimulus_type"] == "prime"
        assert d["valence"] == -0.5

    def test_stimulus_from_dict(self):
        """Test deserialization of Stimulus."""
        data = {
            "stimulus_id": "prime_001",
            "stimulus_type": "prime",
            "file_path": "data/primes/prime_001.png",
            "valence": -0.5,
            "ambiguity": 0.3,
            "metadata": {}
        }
        s = Stimulus.from_dict(data)
        assert s.stimulus_id == "prime_001"
        assert s.stimulus_type == StimulusType.PRIME
        assert s.valence == -0.5


class TestTrial:
    def test_trial_creation(self):
        """Test basic instantiation of Trial."""
        t = Trial(
            trial_id="t_001",
            participant_id="p_001",
            prime_stimulus_id="prime_001",
            target_stimulus_id="target_001",
            response_time_ms=450.5
        )
        assert t.trial_id == "t_001"
        assert t.prime_stimulus_id == "prime_001"
        assert t.response_time_ms == 450.5
        assert t.accuracy is None

    def test_trial_with_accuracy(self):
        """Test Trial with accuracy and condition."""
        t = Trial(
            trial_id="t_001",
            participant_id="p_001",
            prime_stimulus_id="prime_001",
            target_stimulus_id="target_001",
            response_time_ms=450.5,
            accuracy=True,
            prime_condition="congruent"
        )
        assert t.accuracy is True
        assert t.prime_condition == "congruent"

    def test_trial_to_dict(self):
        """Test serialization of Trial."""
        t = Trial(
            trial_id="t_001",
            participant_id="p_001",
            prime_stimulus_id="prime_001",
            target_stimulus_id="target_001",
            response_time_ms=450.5,
            accuracy=True
        )
        d = t.to_dict()
        assert d["trial_id"] == "t_001"
        assert d["accuracy"] is True
        assert d["response_time_ms"] == 450.5

    def test_trial_from_dict(self):
        """Test deserialization of Trial."""
        data = {
            "trial_id": "t_001",
            "participant_id": "p_001",
            "prime_stimulus_id": "prime_001",
            "target_stimulus_id": "target_001",
            "response_time_ms": 450.5,
            "accuracy": True,
            "prime_condition": "incongruent",
            "timestamp": "2023-01-01T10:00:00",
            "metadata": {}
        }
        t = Trial.from_dict(data)
        assert t.trial_id == "t_001"
        assert t.prime_condition == "incongruent"


class TestParticipant:
    def test_participant_creation(self):
        """Test basic instantiation of Participant."""
        p = Participant(participant_id="p_001")
        assert p.participant_id == "p_001"
        assert p.get_trial_count() == 0

    def test_add_trial(self):
        """Test adding a trial to a participant."""
        p = Participant(participant_id="p_001")
        t = Trial(
            trial_id="t_001",
            participant_id="p_001",
            prime_stimulus_id="prime_001",
            target_stimulus_id="target_001",
            response_time_ms=450.5
        )
        p.add_trial(t)
        assert p.get_trial_count() == 1
        assert p.trials[0].trial_id == "t_001"

    def test_participant_to_dict(self):
        """Test serialization of Participant."""
        p = Participant(participant_id="p_001", demographic_data={"age": 25})
        p.add_trial(
            Trial(
                trial_id="t_001",
                participant_id="p_001",
                prime_stimulus_id="prime_001",
                target_stimulus_id="target_001",
                response_time_ms=450.5
            )
        )
        d = p.to_dict()
        assert d["participant_id"] == "p_001"
        assert d["demographic_data"]["age"] == 25
        assert d["trial_count"] == 1


class TestIOHelpers:
    def test_save_and_load_trials(self):
        """Test saving and loading Trial objects to/from JSON."""
        trials = [
            Trial(
                trial_id="t_001",
                participant_id="p_001",
                prime_stimulus_id="prime_001",
                target_stimulus_id="target_001",
                response_time_ms=450.5
            ),
            Trial(
                trial_id="t_002",
                participant_id="p_001",
                prime_stimulus_id="prime_002",
                target_stimulus_id="target_002",
                response_time_ms=520.0
            )
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)

        try:
            save_trials_to_json(trials, temp_path)
            loaded_trials = load_trials_from_json(temp_path)

            assert len(loaded_trials) == 2
            assert loaded_trials[0].trial_id == "t_001"
            assert loaded_trials[1].response_time_ms == 520.0
        finally:
            if temp_path.exists():
                os.unlink(temp_path)

    def test_save_and_load_stimuli(self):
        """Test saving and loading Stimulus objects to/from JSON."""
        stimuli = [
            Stimulus(
                stimulus_id="prime_001",
                stimulus_type=StimulusType.PRIME,
                file_path="data/primes/prime_001.png",
                valence=0.5
            )
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)

        try:
            save_stimuli_to_json(stimuli, temp_path)
            loaded_stimuli = load_stimuli_from_json(temp_path)

            assert len(loaded_stimuli) == 1
            assert loaded_stimuli[0].stimulus_id == "prime_001"
            assert loaded_stimuli[0].valence == 0.5
        finally:
            if temp_path.exists():
                os.unlink(temp_path)