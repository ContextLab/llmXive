"""
Integration tests for the NovelObjectSet generator with PhysicsEnvironment.
"""
import os
import tempfile
import pytest

from generator import NovelObjectSet
from environment import PhysicsEnvironment, create_cpu_environment


class TestGeneratorIntegration:
    """Integration tests for generator with physics environment."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def physics_env(self):
        """Create a CPU-only physics environment."""
        env = create_cpu_environment()
        yield env
        env.reset()

    def test_load_generated_objects_to_simulation(
        self,
        temp_output_dir,
        physics_env
    ):
        """Test that generated objects can be loaded into the physics environment."""
        # Generate objects
        gen = NovelObjectSet(seed=42)
        objects = gen.generate_set(num_objects=3, output_dir=temp_output_dir)

        # Load into simulation
        body_ids = gen.load_objects_for_simulation(physics_env)

        assert len(body_ids) == 3
        for body_id in body_ids:
            assert body_id >= 0  # Valid body ID

    def test_friction_applied_to_objects(
        self,
        temp_output_dir,
        physics_env
    ):
        """Test that friction coefficients are applied to generated objects."""
        import pybullet as p

        # Generate objects with known friction
        gen = NovelObjectSet(seed=42, friction_range=(1.0, 1.0))  # Fixed friction
        objects = gen.generate_set(num_objects=2, output_dir=temp_output_dir)

        # Load into simulation
        body_ids = gen.load_objects_for_simulation(physics_env)

        # Verify friction is set (check base link friction)
        for body_id, obj in zip(body_ids, objects):
            # Get dynamics info for base link (-1)
            dynamics = p.getDynamicsInfo(body_id, -1)
            # lateralFriction is at index 2 in the tuple
            assert abs(dynamics[2] - 1.0) < 0.01

    def test_full_pipeline_generation_and_loading(
        self,
        temp_output_dir,
        physics_env
    ):
        """Test the full pipeline: generate objects and load them."""
        # Generate a larger set
        gen = NovelObjectSet(seed=123, friction_range=(0.2, 1.8))
        num_objects = 10
        objects = gen.generate_set(num_objects=num_objects, output_dir=temp_output_dir)

        # Verify all files exist
        for obj in objects:
            assert os.path.exists(obj["filepath"])

        # Load into simulation
        body_ids = gen.load_objects_for_simulation(physics_env)

        assert len(body_ids) == num_objects

        # Simulate a few steps to ensure stability
        for _ in range(100):
            physics_env.step()

        # Verify objects are still loaded
        for body_id in body_ids:
            assert body_id >= 0
            # Check if position is reasonable (not NaN or Inf)
            pos, _ = physics_env.get_body_position(body_id)
            assert not (pos[0] != pos[0])  # Check for NaN