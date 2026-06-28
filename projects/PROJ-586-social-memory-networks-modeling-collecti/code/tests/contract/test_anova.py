"""Contract test for ANOVA output schema.

This test defines and validates the expected schema for ANOVA analysis
output. It follows TDD: written before implementation to establish
the contract that code/analysis/anova.py (T020) must satisfy.

The ANOVA output schema is designed for two-way independent-samples
ANOVA with factors Context × Metric as specified in FR-006.
"""

import pytest
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import math
import json

@dataclass
class ANOVAOutput:
    """Contract for ANOVA analysis output schema.

    This schema defines the expected structure of ANOVA results
    from code/analysis/anova.py. All fields are required except
    those marked Optional.

    Attributes:
        context_condition: The context factor level ('full' or 'limited')
        metric_type: The metric being analyzed ('specialization_index' or 'retrieval_efficiency')
        f_statistic: The F-statistic value from ANOVA
        p_value: The p-value from the F-test
        degrees_of_freedom: Tuple of (df_between, df_within)
        effect_size: Effect size measure (eta-squared or partial eta-squared)
        sample_size: Number of observations used in analysis
        correction_applied: Type of correction applied (e.g., 'bonferroni')
        alpha_level: Significance threshold for hypothesis testing
        interaction_f_statistic: F-statistic for Context × Metric interaction
        interaction_p_value: p-value for interaction effect
        interaction_effect_size: Effect size for interaction
        main_effect_context_f: F-statistic for context main effect
        main_effect_context_p: p-value for context main effect
        main_effect_metric_f: F-statistic for metric main effect
        main_effect_metric_p: p-value for metric main effect
    """
    context_condition: str
    metric_type: str
    f_statistic: float
    p_value: float
    degrees_of_freedom: Tuple[int, int]
    effect_size: float
    sample_size: Optional[int] = None
    correction_applied: Optional[str] = None
    alpha_level: float = 0.05
    interaction_f_statistic: Optional[float] = None
    interaction_p_value: Optional[float] = None
    interaction_effect_size: Optional[float] = None
    main_effect_context_f: Optional[float] = None
    main_effect_context_p: Optional[float] = None
    main_effect_metric_f: Optional[float] = None
    main_effect_metric_p: Optional[float] = None

    def validate(self) -> bool:
        """Validate the ANOVA output schema.

        Returns:
            bool: True if all required fields are present and valid.
        """
        # Check required string fields
        if not isinstance(self.context_condition, str):
            return False
        if self.context_condition not in ('full', 'limited'):
            return False

        if not isinstance(self.metric_type, str):
            return False
        if self.metric_type not in ('specialization_index', 'retrieval_efficiency'):
            return False

        # Check required numeric fields
        if not isinstance(self.f_statistic, (int, float)):
            return False
        if self.f_statistic < 0:
            return False

        if not isinstance(self.p_value, (int, float)):
            return False
        if not (0 <= self.p_value <= 1):
            return False

        # Check degrees of freedom
        if not isinstance(self.degrees_of_freedom, tuple):
            return False
        if len(self.degrees_of_freedom) != 2:
            return False
        if not all(isinstance(d, int) for d in self.degrees_of_freedom):
            return False
        if any(d < 0 for d in self.degrees_of_freedom):
            return False

        # Check effect size
        if not isinstance(self.effect_size, (int, float)):
            return False
        if not (0 <= self.effect_size <= 1):
            return False

        # Check optional fields if present
        if self.sample_size is not None:
            if not isinstance(self.sample_size, int) or self.sample_size < 1:
                return False

        if self.correction_applied is not None:
            if not isinstance(self.correction_applied, str):
                return False
            if self.correction_applied not in ('bonferroni', 'holm', 'none', None):
                return False

        if not isinstance(self.alpha_level, (int, float)):
            return False
        if not (0 < self.alpha_level < 1):
            return False

        # Check interaction fields if present
        if self.interaction_f_statistic is not None:
            if not isinstance(self.interaction_f_statistic, (int, float)):
                return False
            if self.interaction_f_statistic < 0:
                return False

        if self.interaction_p_value is not None:
            if not isinstance(self.interaction_p_value, (int, float)):
                return False
            if not (0 <= self.interaction_p_value <= 1):
                return False

        if self.interaction_effect_size is not None:
            if not isinstance(self.interaction_effect_size, (int, float)):
                return False
            if not (0 <= self.interaction_effect_size <= 1):
                return False

        # Check main effect fields if present
        for prefix in ('main_effect_context_', 'main_effect_metric_'):
            f_field = getattr(self, f'{prefix}f', None)
            p_field = getattr(self, f'{prefix}p', None)

            if f_field is not None:
                if not isinstance(f_field, (int, float)) or f_field < 0:
                    return False

            if p_field is not None:
                if not isinstance(p_field, (int, float)) or not (0 <= p_field <= 1):
                    return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class TestANOVAOutputSchema:
    """Test cases for ANOVA output schema validation."""

    def test_valid_anova_output_creation(self):
        """Test that a valid ANOVAOutput can be created."""
        output = ANOVAOutput(
            context_condition='full',
            metric_type='specialization_index',
            f_statistic=5.42,
            p_value=0.021,
            degrees_of_freedom=(1, 1998),
            effect_size=0.0027,
            sample_size=2000,
            correction_applied='bonferroni',
            alpha_level=0.05,
            interaction_f_statistic=4.87,
            interaction_p_value=0.027,
            interaction_effect_size=0.0024,
            main_effect_context_f=3.21,
            main_effect_context_p=0.073,
            main_effect_metric_f=6.54,
            main_effect_metric_p=0.011
        )
        assert output.validate() is True

    def test_valid_anova_output_minimal(self):
        """Test that a minimal valid ANOVAOutput can be created."""
        output = ANOVAOutput(
            context_condition='limited',
            metric_type='retrieval_efficiency',
            f_statistic=3.14,
            p_value=0.078,
            degrees_of_freedom=(1, 998),
            effect_size=0.0031
        )
        assert output.validate() is True

    def test_invalid_context_condition(self):
        """Test that invalid context_condition is rejected."""
        with pytest.raises(AssertionError):
            output = ANOVAOutput(
                context_condition='invalid',
                metric_type='specialization_index',
                f_statistic=3.14,
                p_value=0.078,
                degrees_of_freedom=(1, 998),
                effect_size=0.0031
            )
            assert output.validate() is False

    def test_invalid_metric_type(self):
        """Test that invalid metric_type is rejected."""
        output = ANOVAOutput(
            context_condition='full',
            metric_type='invalid_metric',
            f_statistic=3.14,
            p_value=0.078,
            degrees_of_freedom=(1, 998),
            effect_size=0.0031
        )
        assert output.validate() is False

    def test_negative_f_statistic(self):
        """Test that negative f_statistic is rejected."""
        output = ANOVAOutput(
            context_condition='full',
            metric_type='specialization_index',
            f_statistic=-1.0,
            p_value=0.078,
            degrees_of_freedom=(1, 998),
            effect_size=0.0031
        )
        assert output.validate() is False

    def test_invalid_p_value_range(self):
        """Test that p_value outside [0, 1] is rejected."""
        output = ANOVAOutput(
            context_condition='full',
            metric_type='specialization_index',
            f_statistic=3.14,
            p_value=1.5,
            degrees_of_freedom=(1, 998),
            effect_size=0.0031
        )
        assert output.validate() is False

    def test_invalid_degrees_of_freedom_length(self):
        """Test that degrees_of_freedom with wrong length is rejected."""
        output = ANOVAOutput(
            context_condition='full',
            metric_type='specialization_index',
            f_statistic=3.14,
            p_value=0.078,
            degrees_of_freedom=(1,),  # Wrong length
            effect_size=0.0031
        )
        assert output.validate() is False

    def test_negative_degrees_of_freedom(self):
        """Test that negative degrees_of_freedom is rejected."""
        output = ANOVAOutput(
            context_condition='full',
            metric_type='specialization_index',
            f_statistic=3.14,
            p_value=0.078,
            degrees_of_freedom=(1, -1),
            effect_size=0.0031
        )
        assert output.validate() is False

    def test_effect_size_outside_range(self):
        """Test that effect_size outside [0, 1] is rejected."""
        output = ANOVAOutput(
            context_condition='full',
            metric_type='specialization_index',
            f_statistic=3.14,
            p_value=0.078,
            degrees_of_freedom=(1, 998),
            effect_size=1.5  # Outside range
        )
        assert output.validate() is False

    def test_invalid_sample_size(self):
        """Test that invalid sample_size is rejected."""
        output = ANOVAOutput(
            context_condition='full',
            metric_type='specialization_index',
            f_statistic=3.14,
            p_value=0.078,
            degrees_of_freedom=(1, 998),
            effect_size=0.0031,
            sample_size=0  # Invalid
        )
        assert output.validate() is False

    def test_invalid_alpha_level(self):
        """Test that invalid alpha_level is rejected."""
        output = ANOVAOutput(
            context_condition='full',
            metric_type='specialization_index',
            f_statistic=3.14,
            p_value=0.078,
            degrees_of_freedom=(1, 998),
            effect_size=0.0031,
            alpha_level=1.5  # Outside range
        )
        assert output.validate() is False

    def test_serialization_to_dict(self):
        """Test that ANOVAOutput can be serialized to dict."""
        output = ANOVAOutput(
            context_condition='full',
            metric_type='specialization_index',
            f_statistic=5.42,
            p_value=0.021,
            degrees_of_freedom=(1, 1998),
            effect_size=0.0027
        )
        d = output.to_dict()
        assert d['context_condition'] == 'full'
        assert d['metric_type'] == 'specialization_index'
        assert d['f_statistic'] == 5.42
        assert d['p_value'] == 0.021

    def test_serialization_to_json(self):
        """Test that ANOVAOutput can be serialized to JSON."""
        output = ANOVAOutput(
            context_condition='limited',
            metric_type='retrieval_efficiency',
            f_statistic=3.14,
            p_value=0.078,
            degrees_of_freedom=(1, 998),
            effect_size=0.0031
        )
        json_str = output.to_json()
        assert isinstance(json_str, str)
        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed['context_condition'] == 'limited'

    def test_full_contract_output(self):
        """Test the complete ANOVA output contract with all fields."""
        output = ANOVAOutput(
            context_condition='full',
            metric_type='specialization_index',
            f_statistic=5.42,
            p_value=0.021,
            degrees_of_freedom=(1, 1998),
            effect_size=0.0027,
            sample_size=2000,
            correction_applied='bonferroni',
            alpha_level=0.05,
            interaction_f_statistic=4.87,
            interaction_p_value=0.027,
            interaction_effect_size=0.0024,
            main_effect_context_f=3.21,
            main_effect_context_p=0.073,
            main_effect_metric_f=6.54,
            main_effect_metric_p=0.011
        )
        assert output.validate() is True

        # Verify all fields are accessible
        d = output.to_dict()
        assert 'interaction_f_statistic' in d
        assert 'main_effect_context_p' in d
        assert 'correction_applied' in d


class TestANOVAOutputContract:
    """Test cases for the ANOVA output contract requirements."""

    def test_two_way_anova_factors(self):
        """Test that the contract supports two-way ANOVA factors.

        Per FR-006, the ANOVA must have Context × Metric factors.
        This test verifies the schema supports both main effects
        and interaction effects.
        """
        output = ANOVAOutput(
            context_condition='full',
            metric_type='specialization_index',
            f_statistic=5.42,
            p_value=0.021,
            degrees_of_freedom=(1, 1998),
            effect_size=0.0027,
            # Interaction effects (required for two-way ANOVA)
            interaction_f_statistic=4.87,
            interaction_p_value=0.027,
            interaction_effect_size=0.0024,
            # Main effects
            main_effect_context_f=3.21,
            main_effect_context_p=0.073,
            main_effect_metric_f=6.54,
            main_effect_metric_p=0.011
        )
        assert output.validate() is True
        assert output.interaction_f_statistic is not None
        assert output.main_effect_context_f is not None
        assert output.main_effect_metric_f is not None

    def test_bonferroni_correction_support(self):
        """Test that the contract supports Bonferroni correction.

        Per FR-007, Bonferroni correction must be applied to
        family-wise hypothesis tests. This test verifies the
        schema supports recording the correction.
        """
        output = ANOVAOutput(
            context_condition='limited',
            metric_type='retrieval_efficiency',
            f_statistic=3.14,
            p_value=0.078,
            degrees_of_freedom=(1, 998),
            effect_size=0.0031,
            correction_applied='bonferroni',
            alpha_level=0.05 / 4  # Bonferroni-corrected for 4 tests
        )
        assert output.validate() is True
        assert output.correction_applied == 'bonferroni'

    def test_significance_threshold(self):
        """Test that the contract records the significance threshold.

        The alpha_level field must be present and valid for
        determining statistical significance.
        """
        output = ANOVAOutput(
            context_condition='full',
            metric_type='specialization_index',
            f_statistic=5.42,
            p_value=0.021,
            degrees_of_freedom=(1, 1998),
            effect_size=0.0027,
            alpha_level=0.05
        )
        assert output.validate() is True
        assert output.p_value < output.alpha_level  # Significant result

    def test_sample_size_tracking(self):
        """Test that the contract supports sample size tracking.

        Per FR-009, power analysis requires N=1000 games.
        This test verifies the schema can track sample size.
        """
        output = ANOVAOutput(
            context_condition='full',
            metric_type='specialization_index',
            f_statistic=5.42,
            p_value=0.021,
            degrees_of_freedom=(1, 1998),
            effect_size=0.0027,
            sample_size=2000  # 1000 per condition × 2 conditions
        )
        assert output.validate() is True
        assert output.sample_size == 2000


class TestANOVAIntegration:
    """Integration tests for ANOVA output contract."""

    def test_anova_output_as_dict_for_pandas(self):
        """Test that ANOVAOutput can be converted for pandas DataFrame.

        This verifies the contract is compatible with downstream
        analysis that uses pandas for data manipulation.
        """
        outputs = [
            ANOVAOutput(
                context_condition='full',
                metric_type='specialization_index',
                f_statistic=5.42,
                p_value=0.021,
                degrees_of_freedom=(1, 1998),
                effect_size=0.0027
            ),
            ANOVAOutput(
                context_condition='limited',
                metric_type='retrieval_efficiency',
                f_statistic=3.14,
                p_value=0.078,
                degrees_of_freedom=(1, 998),
                effect_size=0.0031
            )
        ]

        # Convert to list of dicts (compatible with pandas)
        dicts = [o.to_dict() for o in outputs]
        assert len(dicts) == 2
        assert all(isinstance(d, dict) for d in dicts)

    def test_anova_output_roundtrip(self):
        """Test that ANOVAOutput can be serialized and deserialized."""
        original = ANOVAOutput(
            context_condition='full',
            metric_type='specialization_index',
            f_statistic=5.42,
            p_value=0.021,
            degrees_of_freedom=(1, 1998),
            effect_size=0.0027,
            sample_size=2000
        )

        # Serialize to JSON
        json_str = original.to_json()

        # Parse JSON back
        parsed = json.loads(json_str)

        # Reconstruct
        reconstructed = ANOVAOutput(
            context_condition=parsed['context_condition'],
            metric_type=parsed['metric_type'],
            f_statistic=parsed['f_statistic'],
            p_value=parsed['p_value'],
            degrees_of_freedom=tuple(parsed['degrees_of_freedom']),
            effect_size=parsed['effect_size'],
            sample_size=parsed['sample_size']
        )

        assert reconstructed.validate() is True
        assert reconstructed.context_condition == original.context_condition
        assert reconstructed.f_statistic == original.f_statistic

    def test_multiple_metric_types(self):
        """Test that the contract supports both metric types."""
        specialization = ANOVAOutput(
            context_condition='full',
            metric_type='specialization_index',
            f_statistic=5.42,
            p_value=0.021,
            degrees_of_freedom=(1, 1998),
            effect_size=0.0027
        )

        retrieval = ANOVAOutput(
            context_condition='limited',
            metric_type='retrieval_efficiency',
            f_statistic=3.14,
            p_value=0.078,
            degrees_of_freedom=(1, 998),
            effect_size=0.0031
        )

        assert specialization.validate() is True
        assert retrieval.validate() is True
        assert specialization.metric_type == 'specialization_index'
        assert retrieval.metric_type == 'retrieval_efficiency'

    def test_multiple_context_conditions(self):
        """Test that the contract supports both context conditions."""
        full = ANOVAOutput(
            context_condition='full',
            metric_type='specialization_index',
            f_statistic=5.42,
            p_value=0.021,
            degrees_of_freedom=(1, 1998),
            effect_size=0.0027
        )

        limited = ANOVAOutput(
            context_condition='limited',
            metric_type='retrieval_efficiency',
            f_statistic=3.14,
            p_value=0.078,
            degrees_of_freedom=(1, 998),
            effect_size=0.0031
        )

        assert full.validate() is True
        assert limited.validate() is True
        assert full.context_condition == 'full'
        assert limited.context_condition == 'limited'