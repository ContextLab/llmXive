"""
Unit tests for the configuration loader (code/config.py).

These tests verify that the default configuration file can be parsed
into a typed Config object and that each field has the expected
Python type.
"""
import os

from config import load_config, Config, TopologyConfig, SolverConfig, ExperimentConfig


def test_load_config_returns_correct_types():
    """
    Load the default configuration and assert the resulting object
    hierarchy has the correct dataclass types and attribute types.
    """
    cfg: Config = load_config()

    # Top‑level Config object
    assert isinstance(cfg, Config)

    # Section objects
    assert isinstance(cfg.topology, TopologyConfig)
    assert isinstance(cfg.solver, SolverConfig)
    assert isinstance(cfg.experiment, ExperimentConfig)

    # TopologyConfig attribute types
    assert isinstance(cfg.topology.min_hinges, int)
    assert isinstance(cfg.topology.max_hinges, int)
    assert isinstance(cfg.topology.stiffness_range, tuple)
    # Ensure each element of the tuple is a float
    assert all(isinstance(v, float) for v in cfg.topology.stiffness_range)

    # SolverConfig attribute types
    assert isinstance(cfg.solver.timeout_per_step_ms, float)
    assert isinstance(cfg.solver.max_retries, int)
    assert isinstance(cfg.solver.retry_backoff_multiplier, float)
    assert isinstance(cfg.solver.initial_retry_delay_s, float)

    # ExperimentConfig attribute types
    assert isinstance(cfg.experiment.seed, int)
    assert isinstance(cfg.experiment.trial_count, int)
    assert isinstance(cfg.experiment.sim_fps, int)
    assert isinstance(cfg.experiment.timeout_limits, float)
    assert isinstance(cfg.experiment.topology_counts, list)
    # Ensure list elements are ints
    assert all(isinstance(v, int) for v in cfg.experiment.topology_counts)