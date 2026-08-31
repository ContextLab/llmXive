"""
Tests for the Physics Oracle module (T006).

These tests verify that:
1. Mass and energy deviations are correctly calculated and logged.
2. Stability bounds are checked and violations are recorded.
3. MetricRecord objects contain the required violation details.
"""
import pytest
import math
from src.sim.physics_oracle import (
    PhysicsOracle, 
    PhysicsOracleConfig, 
    PhysicsViolation,
    validate_physics_constraints,
    run_physics_validation
)
from src.data_models import MetricRecord


class TestPhysicsOracle:
    """Unit tests for PhysicsOracle class."""

    def test_init_default_config(self):
        """Test that default configuration is applied."""
        oracle = PhysicsOracle()
        assert oracle.config.mass_tolerance == 0.05
        assert oracle.config.energy_tolerance == 0.10
        assert oracle.config.stability_threshold == 100.0

    def test_init_custom_config(self):
        """Test that custom configuration is applied."""
        custom_config = PhysicsOracleConfig(
            mass_tolerance=0.01,
            energy_tolerance=0.05,
            stability_threshold=50.0
        )
        oracle = PhysicsOracle(custom_config)
        assert oracle.config.mass_tolerance == 0.01
        assert oracle.config.energy_tolerance == 0.05
        assert oracle.config.stability_threshold == 50.0

    def test_validate_step_no_violations(self):
        """Test validation when no physics violations occur."""
        oracle = PhysicsOracle()
        state = {
            'particles': [
                {'mass': 1.0, 'velocity': 1.0, 'position': 1.0},
                {'mass': 2.0, 'velocity': 2.0, 'position': 2.0}
            ]
        }
        
        record = oracle.validate_step(step_id=1, state=state)
        
        assert isinstance(record, MetricRecord)
        assert record.metrics['physics_valid'] is True
        assert record.metrics['violation_count'] == 0
        assert record.metrics['stable'] is True

    def test_validate_step_mass_violation(self):
        """Test detection of mass conservation violation."""
        oracle = PhysicsOracle(PhysicsOracleConfig(mass_tolerance=0.01))
        
        # Initial state
        state1 = {
            'particles': [
                {'mass': 100.0, 'velocity': 1.0, 'position': 1.0}
            ]
        }
        oracle.validate_step(step_id=1, state=state1)
        
        # Second state with significant mass change (10% deviation)
        state2 = {
            'particles': [
                {'mass': 110.0, 'velocity': 1.0, 'position': 1.0}
            ]
        }
        
        record = oracle.validate_step(step_id=2, state=state2)
        
        assert record.metrics['physics_valid'] is False
        assert record.metrics['violation_count'] == 1
        assert any(v['type'] == 'mass_deviation' for v in record.metrics['violation_details'])
        assert 'mass_deviation_2' in record.metrics

    def test_validate_step_energy_violation(self):
        """Test detection of energy conservation violation."""
        oracle = PhysicsOracle(PhysicsOracleConfig(energy_tolerance=0.01))
        
        # Initial state
        state1 = {
            'particles': [
                {'mass': 1.0, 'velocity': 10.0, 'position': 0.0}
            ]
        }
        oracle.validate_step(step_id=1, state=state1)
        
        # Second state with significant energy change (velocity doubled)
        state2 = {
            'particles': [
                {'mass': 1.0, 'velocity': 20.0, 'position': 0.0}
            ]
        }
        
        record = oracle.validate_step(step_id=2, state=state2)
        
        assert record.metrics['physics_valid'] is False
        assert record.metrics['violation_count'] == 1
        assert any(v['type'] == 'energy_drift' for v in record.metrics['violation_details'])
        assert 'energy_deviation_2' in record.metrics

    def test_validate_step_stability_breach(self):
        """Test detection of stability threshold breach."""
        oracle = PhysicsOracle(PhysicsOracleConfig(stability_threshold=5.0))
        
        # State with magnitude exceeding threshold
        state = {
            'particles': [
                {'mass': 1.0, 'velocity': 10.0, 'position': 10.0}
            ]
        }
        
        record = oracle.validate_step(step_id=1, state=state)
        
        assert record.metrics['stable'] is False
        assert record.metrics['physics_valid'] is False
        assert any(v['type'] == 'stability_breach' for v in record.metrics['violation_details'])

    def test_multiple_violations_same_step(self):
        """Test detection of multiple violations in one step."""
        oracle = PhysicsOracle(PhysicsOracleConfig(
            mass_tolerance=0.01,
            energy_tolerance=0.01,
            stability_threshold=5.0
        ))
        
        # Set initial state
        state1 = {
            'particles': [
                {'mass': 100.0, 'velocity': 1.0, 'position': 1.0}
            ]
        }
        oracle.validate_step(step_id=1, state=state1)
        
        # State with mass, energy, and stability violations
        state2 = {
            'particles': [
                {'mass': 120.0, 'velocity': 100.0, 'position': 100.0}
            ]
        }
        
        record = oracle.validate_step(step_id=2, state=state2)
        
        assert record.metrics['violation_count'] >= 3  # Mass, Energy, Stability

    def test_violation_summary(self):
        """Test the violation summary functionality."""
        oracle = PhysicsOracle()
        
        # Generate some violations
        state1 = {'particles': [{'mass': 100.0, 'velocity': 1.0, 'position': 1.0}]}
        oracle.validate_step(step_id=1, state=state1)
        
        state2 = {'particles': [{'mass': 150.0, 'velocity': 1.0, 'position': 1.0}]}
        oracle.validate_step(step_id=2, state=state2)
        
        summary = oracle.get_violation_summary()
        
        assert summary['total_violations'] > 0
        assert 'by_type' in summary
        assert 'by_severity' in summary
        assert 'details' in summary

    def test_reset(self):
        """Test that reset clears oracle state."""
        oracle = PhysicsOracle()
        
        state = {'particles': [{'mass': 100.0, 'velocity': 100.0, 'position': 100.0}]}
        oracle.validate_step(step_id=1, state=state)
        
        assert oracle.get_violation_summary()['total_violations'] > 0
        
        oracle.reset()
        
        assert oracle.get_violation_summary()['total_violations'] == 0
        assert oracle._last_total_mass is None
        assert oracle._last_total_energy is None


class TestValidatePhysicsConstraints:
    """Tests for the convenience function validate_physics_constraints."""

    def test_convenience_function(self):
        """Test that the convenience function works correctly."""
        state = {
            'particles': [
                {'mass': 1.0, 'velocity': 1.0, 'position': 1.0}
            ]
        }
        
        record = validate_physics_constraints(step_id=1, state=state, seed=42)
        
        assert isinstance(record, MetricRecord)
        assert record.step_id == 1
        assert 'physics_valid' in record.metrics

    def test_convenience_function_with_violations(self):
        """Test convenience function with violation detection."""
        oracle = PhysicsOracle(PhysicsOracleConfig(stability_threshold=1.0))
        
        state = {
            'particles': [
                {'mass': 1.0, 'velocity': 10.0, 'position': 10.0}
            ]
        }
        
        record = validate_physics_constraints(step_id=1, state=state, seed=42)
        
        assert record.metrics['stable'] is False
        assert record.metrics['physics_valid'] is False


class TestRunPhysicsValidation:
    """Tests for the batch validation function."""

    def test_batch_validation(self):
        """Test validation over multiple steps."""
        steps = [
            (1, {'particles': [{'mass': 1.0, 'velocity': 1.0, 'position': 1.0}]}),
            (2, {'particles': [{'mass': 1.0, 'velocity': 1.0, 'position': 1.0}]}),
            (3, {'particles': [{'mass': 1.0, 'velocity': 1.0, 'position': 1.0}]}),
        ]
        
        records = run_physics_validation(steps, seed=42)
        
        assert len(records) == 3
        assert all(isinstance(r, MetricRecord) for r in records)
        assert all(r.step_id == i+1 for i, r in enumerate(records))

    def test_batch_validation_with_violations(self):
        """Test batch validation with injected violations."""
        steps = [
            (1, {'particles': [{'mass': 100.0, 'velocity': 1.0, 'position': 1.0}]}),
            (2, {'particles': [{'mass': 150.0, 'velocity': 100.0, 'position': 100.0}]}),  # Violations
        ]
        
        config = PhysicsOracleConfig(
            mass_tolerance=0.01,
            energy_tolerance=0.01,
            stability_threshold=5.0
        )
        
        records = run_physics_validation(steps, config=config, seed=42)
        
        assert len(records) == 2
        assert records[0].metrics['physics_valid'] is True
        assert records[1].metrics['physics_valid'] is False
        assert records[1].metrics['violation_count'] >= 3