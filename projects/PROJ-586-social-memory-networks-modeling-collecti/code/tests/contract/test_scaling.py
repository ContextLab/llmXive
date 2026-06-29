"""
Contract tests for scaling analysis plot schema (User Story 3).

These tests verify the schema of scaling analysis outputs including:
- Power-law fitting parameters
- Confidence intervals for exponent β
- Agent count vs. metric relationships
- Plot metadata and schema validation

Per reviewer Geoffrey West's feedback on scaling laws in complex systems,
this analysis tests whether collective remembering follows power-law scaling
similar to urban infrastructure (N^0.85 sublinear scaling).
"""
import pytest
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, asdict
import json
import math
import os
from pathlib import Path

@dataclass
class ScalingAnalysisResult:
    """Schema for scaling analysis output (T027-T030).
    
    This dataclass defines the contract for scaling analysis results
    that will be produced by code/analysis/scaling.py.
    
    Attributes:
        agent_counts: List of agent counts tested (e.g., [3, 5, 7])
        specialization_indices: Mean specialization index for each agent count
        retrieval_efficiencies: Mean retrieval efficiency for each agent count
        power_law_exponent: Fitted exponent β for power-law relationship
        confidence_interval_lower: Lower bound of 95% CI for β
        confidence_interval_upper: Upper bound of 95% CI for β
        num_games_per_count: Number of games simulated per agent count
        sublinear_scaling: True if β < 1 (per Geoffrey West's urban scaling)
        plot_path: Path to generated scaling_plot.pdf
        r_squared: R² value for power-law fit
        fitted_coefficient: Pre-exponential coefficient for power-law
    """
    agent_counts: List[int]
    specialization_indices: List[float]
    retrieval_efficiencies: List[float]
    power_law_exponent: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    num_games_per_count: int
    sublinear_scaling: bool
    plot_path: str
    r_squared: float
    fitted_coefficient: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    def validate(self) -> bool:
        """Validate the scaling analysis result schema.
        
        Returns:
            True if all schema requirements are met.
        """
        # Check minimum agent counts (need at least 2 for any scaling analysis)
        if len(self.agent_counts) < 2:
            return False
        
        # Check list lengths match
        if len(self.agent_counts) != len(self.specialization_indices):
            return False
        if len(self.agent_counts) != len(self.retrieval_efficiencies):
            return False
        
        # Check all values are finite
        if not all(math.isfinite(x) for x in self.specialization_indices):
            return False
        if not all(math.isfinite(x) for x in self.retrieval_efficiencies):
            return False
        if not math.isfinite(self.power_law_exponent):
            return False
        if not math.isfinite(self.confidence_interval_lower):
            return False
        if not math.isfinite(self.confidence_interval_upper):
            return False
        if not math.isfinite(self.r_squared):
            return False
        
        # Check confidence interval is valid
        if self.confidence_interval_lower >= self.confidence_interval_upper:
            return False
        
        # Check R² is in valid range
        if not (0.0 <= self.r_squared <= 1.0):
            return False
        
        # Check agent counts are positive
        if not all(count > 0 for count in self.agent_counts):
            return False
        
        # Check num_games_per_count is positive
        if self.num_games_per_count <= 0:
            return False
        
        # Check plot_path is non-empty
        if not self.plot_path:
            return False
        
        return True
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ScalingAnalysisResult':
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls(**data)

class TestScalingAnalysisResultSchema:
    """Test the ScalingAnalysisResult dataclass schema."""
    
    def test_required_fields_exist(self):
        """Verify all required fields are present in the schema."""
        result = ScalingAnalysisResult(
            agent_counts=[3, 5, 7],
            specialization_indices=[0.5, 0.7, 0.9],
            retrieval_efficiencies=[0.8, 0.85, 0.9],
            power_law_exponent=0.85,
            confidence_interval_lower=0.70,
            confidence_interval_upper=1.00,
            num_games_per_count=800,
            sublinear_scaling=True,
            plot_path="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf",
            r_squared=0.95,
            fitted_coefficient=0.5
        )
        
        # Verify all fields are accessible
        assert hasattr(result, 'agent_counts')
        assert hasattr(result, 'specialization_indices')
        assert hasattr(result, 'retrieval_efficiencies')
        assert hasattr(result, 'power_law_exponent')
        assert hasattr(result, 'confidence_interval_lower')
        assert hasattr(result, 'confidence_interval_upper')
        assert hasattr(result, 'num_games_per_count')
        assert hasattr(result, 'sublinear_scaling')
        assert hasattr(result, 'plot_path')
        assert hasattr(result, 'r_squared')
        assert hasattr(result, 'fitted_coefficient')
    
    def test_to_dict_serialization(self):
        """Test that to_dict produces valid dictionary."""
        result = ScalingAnalysisResult(
            agent_counts=[3, 5, 7],
            specialization_indices=[0.5, 0.7, 0.9],
            retrieval_efficiencies=[0.8, 0.85, 0.9],
            power_law_exponent=0.85,
            confidence_interval_lower=0.70,
            confidence_interval_upper=1.00,
            num_games_per_count=800,
            sublinear_scaling=True,
            plot_path="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf",
            r_squared=0.95,
            fitted_coefficient=0.5
        )
        
        d = result.to_dict()
        assert isinstance(d, dict)
        assert 'agent_counts' in d
        assert 'power_law_exponent' in d
        assert 'confidence_interval_lower' in d
        assert 'confidence_interval_upper' in d
    
    def test_to_json_roundtrip(self):
        """Test JSON serialization and deserialization."""
        result = ScalingAnalysisResult(
            agent_counts=[3, 5, 7],
            specialization_indices=[0.5, 0.7, 0.9],
            retrieval_efficiencies=[0.8, 0.85, 0.9],
            power_law_exponent=0.85,
            confidence_interval_lower=0.70,
            confidence_interval_upper=1.00,
            num_games_per_count=800,
            sublinear_scaling=True,
            plot_path="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf",
            r_squared=0.95,
            fitted_coefficient=0.5
        )
        
        json_str = result.to_json()
        assert isinstance(json_str, str)
        
        restored = ScalingAnalysisResult.from_json(json_str)
        assert restored.agent_counts == result.agent_counts
        assert restored.power_law_exponent == result.power_law_exponent
        assert restored.confidence_interval_lower == result.confidence_interval_lower
        assert restored.confidence_interval_upper == result.confidence_interval_upper

class TestScalingAnalysisValidation:
    """Test the validate() method of ScalingAnalysisResult."""
    
    def test_valid_result_passes(self):
        """A properly formed result should validate successfully."""
        result = ScalingAnalysisResult(
            agent_counts=[3, 5, 7],
            specialization_indices=[0.5, 0.7, 0.9],
            retrieval_efficiencies=[0.8, 0.85, 0.9],
            power_law_exponent=0.85,
            confidence_interval_lower=0.70,
            confidence_interval_upper=1.00,
            num_games_per_count=800,
            sublinear_scaling=True,
            plot_path="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf",
            r_squared=0.95,
            fitted_coefficient=0.5
        )
        
        assert result.validate() is True
    
    def test_insufficient_agent_counts_fails(self):
        """Less than 2 agent counts should fail validation."""
        result = ScalingAnalysisResult(
            agent_counts=[3],
            specialization_indices=[0.5],
            retrieval_efficiencies=[0.8],
            power_law_exponent=0.85,
            confidence_interval_lower=0.70,
            confidence_interval_upper=1.00,
            num_games_per_count=800,
            sublinear_scaling=True,
            plot_path="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf",
            r_squared=0.95,
            fitted_coefficient=0.5
        )
        
        assert result.validate() is False
    
    def test_mismatched_list_lengths_fail(self):
        """Mismatched list lengths should fail validation."""
        result = ScalingAnalysisResult(
            agent_counts=[3, 5, 7],
            specialization_indices=[0.5, 0.7],  # Only 2 instead of 3
            retrieval_efficiencies=[0.8, 0.85, 0.9],
            power_law_exponent=0.85,
            confidence_interval_lower=0.70,
            confidence_interval_upper=1.00,
            num_games_per_count=800,
            sublinear_scaling=True,
            plot_path="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf",
            r_squared=0.95,
            fitted_coefficient=0.5
        )
        
        assert result.validate() is False
    
    def test_invalid_confidence_interval_fails(self):
        """Confidence interval where lower >= upper should fail."""
        result = ScalingAnalysisResult(
            agent_counts=[3, 5, 7],
            specialization_indices=[0.5, 0.7, 0.9],
            retrieval_efficiencies=[0.8, 0.85, 0.9],
            power_law_exponent=0.85,
            confidence_interval_lower=1.00,  # Invalid: >= upper
            confidence_interval_upper=0.70,
            num_games_per_count=800,
            sublinear_scaling=True,
            plot_path="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf",
            r_squared=0.95,
            fitted_coefficient=0.5
        )
        
        assert result.validate() is False
    
    def test_invalid_r_squared_fails(self):
        """R² outside [0, 1] should fail validation."""
        result = ScalingAnalysisResult(
            agent_counts=[3, 5, 7],
            specialization_indices=[0.5, 0.7, 0.9],
            retrieval_efficiencies=[0.8, 0.85, 0.9],
            power_law_exponent=0.85,
            confidence_interval_lower=0.70,
            confidence_interval_upper=1.00,
            num_games_per_count=800,
            sublinear_scaling=True,
            plot_path="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf",
            r_squared=1.5,  # Invalid: > 1
            fitted_coefficient=0.5
        )
        
        assert result.validate() is False
    
    def test_non_finite_values_fail(self):
        """Non-finite values should fail validation."""
        result = ScalingAnalysisResult(
            agent_counts=[3, 5, 7],
            specialization_indices=[float('inf'), 0.7, 0.9],  # Invalid
            retrieval_efficiencies=[0.8, 0.85, 0.9],
            power_law_exponent=0.85,
            confidence_interval_lower=0.70,
            confidence_interval_upper=1.00,
            num_games_per_count=800,
            sublinear_scaling=True,
            plot_path="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf",
            r_squared=0.95,
            fitted_coefficient=0.5
        )
        
        assert result.validate() is False
    
    def test_empty_plot_path_fails(self):
        """Empty plot path should fail validation."""
        result = ScalingAnalysisResult(
            agent_counts=[3, 5, 7],
            specialization_indices=[0.5, 0.7, 0.9],
            retrieval_efficiencies=[0.8, 0.85, 0.9],
            power_law_exponent=0.85,
            confidence_interval_lower=0.70,
            confidence_interval_upper=1.00,
            num_games_per_count=800,
            sublinear_scaling=True,
            plot_path="",  # Invalid
            r_squared=0.95,
            fitted_coefficient=0.5
        )
        
        assert result.validate() is False
    
    def test_non_positive_games_fails(self):
        """Non-positive num_games_per_count should fail validation."""
        result = ScalingAnalysisResult(
            agent_counts=[3, 5, 7],
            specialization_indices=[0.5, 0.7, 0.9],
            retrieval_efficiencies=[0.8, 0.85, 0.9],
            power_law_exponent=0.85,
            confidence_interval_lower=0.70,
            confidence_interval_upper=1.00,
            num_games_per_count=0,  # Invalid
            sublinear_scaling=True,
            plot_path="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf",
            r_squared=0.95,
            fitted_coefficient=0.5
        )
        
        assert result.validate() is False
    
    def test_non_positive_agent_counts_fail(self):
        """Non-positive agent counts should fail validation."""
        result = ScalingAnalysisResult(
            agent_counts=[3, 5, -1],  # Invalid: -1
            specialization_indices=[0.5, 0.7, 0.9],
            retrieval_efficiencies=[0.8, 0.85, 0.9],
            power_law_exponent=0.85,
            confidence_interval_lower=0.70,
            confidence_interval_upper=1.00,
            num_games_per_count=800,
            sublinear_scaling=True,
            plot_path="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf",
            r_squared=0.95,
            fitted_coefficient=0.5
        )
        
        assert result.validate() is False

class TestScalingAnalysisIntegration:
    """Integration tests for scaling analysis contract."""
    
    def test_schema_matches_implementation_expectations(self):
        """Verify schema matches what scaling.py (T028-T030) should produce."""
        # This test documents the expected output format
        # The actual implementation will be in code/analysis/scaling.py
        
        # Per T028: power-law fitting for metric trends vs. agent count
        # Per T029: 95% confidence interval for exponent β
        # Per T030: scaling_plot.pdf generation with fitted curves
        
        # Expected fields based on task requirements:
        expected_fields = {
            'agent_counts',           # T027: agent counts 3, 5, 7
            'specialization_indices', # T027: specialization metric
            'retrieval_efficiencies', # T027: retrieval metric
            'power_law_exponent',     # T028: fitted β
            'confidence_interval_lower',  # T029: 95% CI lower
            'confidence_interval_upper',  # T029: 95% CI upper
            'num_games_per_count',    # T027: 800 games per config
            'sublinear_scaling',      # T029: β < 1 indicator
            'plot_path',              # T030: scaling_plot.pdf path
            'r_squared',              # T028: fit quality
            'fitted_coefficient'      # T028: pre-exponential factor
        }
        
        actual_fields = set(ScalingAnalysisResult.__dataclass_fields__.keys())
        
        assert expected_fields.issubset(actual_fields), \
            f"Missing fields: {expected_fields - actual_fields}"
    
    def test_sublinear_scaling_flag_logic(self):
        """Verify sublinear_scaling flag reflects β < 1."""
        # When β < 1, scaling is sublinear (like Geoffrey West's urban scaling)
        result_sublinear = ScalingAnalysisResult(
            agent_counts=[3, 5, 7],
            specialization_indices=[0.5, 0.7, 0.9],
            retrieval_efficiencies=[0.8, 0.85, 0.9],
            power_law_exponent=0.85,  # < 1
            confidence_interval_lower=0.70,
            confidence_interval_upper=1.00,
            num_games_per_count=800,
            sublinear_scaling=True,   # Correct: β < 1
            plot_path="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf",
            r_squared=0.95,
            fitted_coefficient=0.5
        )
        assert result_sublinear.sublinear_scaling is True
        
        # When β >= 1, scaling is not sublinear
        result_linear = ScalingAnalysisResult(
            agent_counts=[3, 5, 7],
            specialization_indices=[0.5, 0.7, 0.9],
            retrieval_efficiencies=[0.8, 0.85, 0.9],
            power_law_exponent=1.1,  # >= 1
            confidence_interval_lower=0.90,
            confidence_interval_upper=1.30,
            num_games_per_count=800,
            sublinear_scaling=False,  # Correct: β >= 1
            plot_path="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf",
            r_squared=0.95,
            fitted_coefficient=0.5
        )
        assert result_linear.sublinear_scaling is False
    
    def test_confidence_interval_interpretation(self):
        """Verify CI bounds interpretation for power analysis."""
        # Per T029: 95% CI for exponent β
        # If CI includes 1.0, we cannot reject linear scaling
        # If CI is entirely below 1.0, we have evidence of sublinear scaling
        
        ci_excludes_one = ScalingAnalysisResult(
            agent_counts=[3, 5, 7],
            specialization_indices=[0.5, 0.7, 0.9],
            retrieval_efficiencies=[0.8, 0.85, 0.9],
            power_law_exponent=0.85,
            confidence_interval_lower=0.70,
            confidence_interval_upper=0.99,  # Entirely below 1.0
            num_games_per_count=800,
            sublinear_scaling=True,
            plot_path="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf",
            r_squared=0.95,
            fitted_coefficient=0.5
        )
        
        # Evidence of sublinear scaling (CI does not include 1.0)
        assert ci_excludes_one.confidence_interval_upper < 1.0
        
        ci_includes_one = ScalingAnalysisResult(
            agent_counts=[3, 5, 7],
            specialization_indices=[0.5, 0.7, 0.9],
            retrieval_efficiencies=[0.8, 0.85, 0.9],
            power_law_exponent=0.95,
            confidence_interval_lower=0.80,
            confidence_interval_upper=1.10,  # Includes 1.0
            num_games_per_count=800,
            sublinear_scaling=True,
            plot_path="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf",
            r_squared=0.95,
            fitted_coefficient=0.5
        )
        
        # Cannot reject linear scaling (CI includes 1.0)
        assert ci_includes_one.confidence_interval_lower < 1.0 < ci_includes_one.confidence_interval_upper

class TestScalingPlotSchema:
    """Test the scaling plot output schema (T030)."""
    
    def test_plot_path_format(self):
        """Verify plot path follows expected format."""
        result = ScalingAnalysisResult(
            agent_counts=[3, 5, 7],
            specialization_indices=[0.5, 0.7, 0.9],
            retrieval_efficiencies=[0.8, 0.85, 0.9],
            power_law_exponent=0.85,
            confidence_interval_lower=0.70,
            confidence_interval_upper=1.00,
            num_games_per_count=800,
            sublinear_scaling=True,
            plot_path="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf",
            r_squared=0.95,
            fitted_coefficient=0.5
        )
        
        # Per T030: output scaling_plot.pdf to results directory
        assert result.plot_path.endswith('.pdf')
        assert 'scaling_plot' in result.plot_path
        assert 'results' in result.plot_path
    
    def test_plot_metadata_inclusion(self):
        """Verify plot metadata can be included in result."""
        # The plot should include:
        # - Fitted power-law curves
        # - Explicit note about 3 data points limiting reliability
        # - Agent counts on x-axis, metrics on y-axis
        
        result = ScalingAnalysisResult(
            agent_counts=[3, 5, 7],
            specialization_indices=[0.5, 0.7, 0.9],
            retrieval_efficiencies=[0.8, 0.85, 0.9],
            power_law_exponent=0.85,
            confidence_interval_lower=0.70,
            confidence_interval_upper=1.00,
            num_games_per_count=800,
            sublinear_scaling=True,
            plot_path="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf",
            r_squared=0.95,
            fitted_coefficient=0.5
        )
        
        # All metadata fields present for plot annotation
        assert result.power_law_exponent == 0.85
        assert result.r_squared == 0.95
        assert result.fitted_coefficient == 0.5
        assert len(result.agent_counts) == 3  # 3 data points as per T027
    
    def test_agent_count_specification(self):
        """Verify agent counts match T027 specification (3, 5, 7)."""
        result = ScalingAnalysisResult(
            agent_counts=[3, 5, 7],
            specialization_indices=[0.5, 0.7, 0.9],
            retrieval_efficiencies=[0.8, 0.85, 0.9],
            power_law_exponent=0.85,
            confidence_interval_lower=0.70,
            confidence_interval_upper=1.00,
            num_games_per_count=800,
            sublinear_scaling=True,
            plot_path="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf",
            r_squared=0.95,
            fitted_coefficient=0.5
        )
        
        # Per T027: agent counts 3, 5, 7
        assert result.agent_counts == [3, 5, 7]
        assert result.num_games_per_count == 800  # Per T027: 800 games per config

class TestScalingAnalysisEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_minimum_valid_configuration(self):
        """Test minimum valid configuration (2 agent counts)."""
        result = ScalingAnalysisResult(
            agent_counts=[2, 4],
            specialization_indices=[0.4, 0.6],
            retrieval_efficiencies=[0.7, 0.8],
            power_law_exponent=0.85,
            confidence_interval_lower=0.70,
            confidence_interval_upper=1.00,
            num_games_per_count=800,
            sublinear_scaling=True,
            plot_path="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf",
            r_squared=0.95,
            fitted_coefficient=0.5
        )
        
        assert result.validate() is True
    
    def test_zero_r_squared(self):
        """Test R² = 0 (no fit)."""
        result = ScalingAnalysisResult(
            agent_counts=[3, 5, 7],
            specialization_indices=[0.5, 0.7, 0.9],
            retrieval_efficiencies=[0.8, 0.85, 0.9],
            power_law_exponent=0.85,
            confidence_interval_lower=0.70,
            confidence_interval_upper=1.00,
            num_games_per_count=800,
            sublinear_scaling=True,
            plot_path="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf",
            r_squared=0.0,
            fitted_coefficient=0.5
        )
        
        assert result.validate() is True
        assert result.r_squared == 0.0
    
    def test_perfect_fit(self):
        """Test R² = 1 (perfect fit)."""
        result = ScalingAnalysisResult(
            agent_counts=[3, 5, 7],
            specialization_indices=[0.5, 0.7, 0.9],
            retrieval_efficiencies=[0.8, 0.85, 0.9],
            power_law_exponent=0.85,
            confidence_interval_lower=0.70,
            confidence_interval_upper=1.00,
            num_games_per_count=800,
            sublinear_scaling=True,
            plot_path="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf",
            r_squared=1.0,
            fitted_coefficient=0.5
        )
        
        assert result.validate() is True
        assert result.r_squared == 1.0
    
    def test_exactly_linear_scaling(self):
        """Test β = 1.0 (exactly linear)."""
        result = ScalingAnalysisResult(
            agent_counts=[3, 5, 7],
            specialization_indices=[0.5, 0.7, 0.9],
            retrieval_efficiencies=[0.8, 0.85, 0.9],
            power_law_exponent=1.0,
            confidence_interval_lower=0.90,
            confidence_interval_upper=1.10,
            num_games_per_count=800,
            sublinear_scaling=False,
            plot_path="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf",
            r_squared=0.95,
            fitted_coefficient=0.5
        )
        
        assert result.validate() is True
        assert result.sublinear_scaling is False
        assert result.power_law_exponent == 1.0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])