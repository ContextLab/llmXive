"""
Unit tests for ThermalConductivityEstimator (Task T015).

Verifies:
1. Conductivity is estimated using Callaway model (defect density), not graph metrics.
2. Pure crystals have high conductivity.
3. Disordered alloys have reduced conductivity.
4. The correlation between defect density and conductivity is negative (as expected).
"""
import pytest
import numpy as np
from code.synthetic import ThermalConductivityEstimator
from code.utils import DataIntegrityError

class TestThermalConductivityEstimator:
    def test_pure_crystal_high_conductivity(self):
        """Test that a pure crystal (no defects) has base conductivity."""
        estimator = ThermalConductivityEstimator(base_conductivity=400.0, alpha_scattering=0.01)
        
        species = ["Cu"] * 100
        positions = [[i, 0, 0] for i in range(100)]
        volume = 1000.0
        
        kappa = estimator.estimate_conductivity(species, positions, volume)
        
        # Should be close to base conductivity (reduction factor ~ 1.0)
        assert kappa >= 390.0, f"Pure crystal conductivity {kappa} should be near base 400"

    def test_disordered_alloy_reduced_conductivity(self):
        """Test that a 50/50 mix reduces conductivity."""
        estimator = ThermalConductivityEstimator(base_conductivity=400.0, alpha_scattering=0.05)
        
        # 50 Cu, 50 Ni
        species = ["Cu"] * 50 + ["Ni"] * 50
        positions = [[i, 0, 0] for i in range(100)]
        volume = 1000.0
        
        kappa = estimator.estimate_conductivity(species, positions, volume)
        
        # Should be significantly lower than base
        assert kappa < 400.0, f"Disordered alloy conductivity {kappa} should be lower than base"

    def test_defect_density_calculation(self):
        """Test defect density calculation logic."""
        estimator = ThermalConductivityEstimator()
        
        # Pure
        dd_pure = estimator.calculate_defect_density(["Cu"]*10, [[0,0,0]]*10, 100.0)
        assert dd_pure == 0.0, "Pure crystal should have 0 defect density"
        
        # Mixed
        dd_mixed = estimator.calculate_defect_density(["Cu"]*5 + ["Ni"]*5, [[0,0,0]]*10, 100.0)
        assert dd_mixed > 0.0, "Mixed alloy should have > 0 defect density"

    def test_conductivity_monotonicity(self):
        """Test that increasing defect density decreases conductivity."""
        estimator = ThermalConductivityEstimator(base_conductivity=400.0, alpha_scattering=0.02)
        
        base_pos = [[i, 0, 0] for i in range(100)]
        volume = 1000.0
        
        # 0% defect (pure)
        kappa_0 = estimator.estimate_conductivity(["Cu"]*100, base_pos, volume)
        
        # 50% defect (mixed)
        kappa_50 = estimator.estimate_conductivity(["Cu"]*50 + ["Ni"]*50, base_pos, volume)
        
        # 100% defect (fully mixed - same as 50% in this simple model, but conceptually)
        # We test the trend: more disorder -> less conductivity
        assert kappa_0 > kappa_50, "Conductivity must decrease with disorder"

    def test_callaway_model_parameters(self):
        """Test that parameters are applied correctly."""
        # High alpha -> strong reduction
        est_strong = ThermalConductivityEstimator(base_conductivity=400.0, alpha_scattering=1.0)
        # Low alpha -> weak reduction
        est_weak = ThermalConductivityEstimator(base_conductivity=400.0, alpha_scattering=0.0001)
        
        species = ["Cu"]*50 + ["Ni"]*50
        positions = [[i, 0, 0] for i in range(100)]
        volume = 1000.0
        
        kappa_strong = est_strong.estimate_conductivity(species, positions, volume)
        kappa_weak = est_weak.estimate_conductivity(species, positions, volume)
        
        assert kappa_strong < kappa_weak, "Strong scattering should yield lower conductivity"