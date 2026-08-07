"""
Unit tests for base data models.
"""
import pytest
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.models import PhysicalScenario, LatentVector, CounterfactualEdit


def test_physical_scenario_creation():
    """Test creation of a PhysicalScenario."""
    scenario = PhysicalScenario(
        video_id="vid_001",
        original_outcome="object_fell",
        optical_flow_magnitude=0.8
    )
    assert scenario.video_id == "vid_001"
    assert scenario.original_outcome == "object_fell"
    assert scenario.optical_flow_magnitude == 0.8
    assert scenario.scenario_id is not None


def test_latent_vector_creation():
    """Test creation of a LatentVector."""
    vec = np.random.rand(768).astype(np.float32)
    latent = LatentVector(
        scenario_id="scen_001",
        vector=vec
    )
    assert latent.embedding_dim == 768
    assert isinstance(latent.vector, np.ndarray)


def test_latent_vector_from_list():
    """Test LatentVector creation from a list."""
    latent = LatentVector(
        scenario_id="scen_002",
        vector=[1.0, 2.0, 3.0]
    )
    assert latent.embedding_dim == 3
    assert np.array_equal(latent.vector, np.array([1.0, 2.0, 3.0]))


def test_counterfactual_edit_creation():
    """Test creation of a CounterfactualEdit."""
    cf_vec = np.random.rand(768).astype(np.float32)
    edit = CounterfactualEdit(
        original_vector_id="lat_001",
        counterfactual_vector=cf_vec,
        prompt="What if the object floated?",
        ambiguity_flag=0
    )
    assert edit.ambiguity_flag == 0
    assert edit.prompt == "What if the object floated?"
    assert edit.method == "vector_arithmetic"