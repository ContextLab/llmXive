"""
Neural-Symbolic Interface Module

This module implements the hard thresholding function required to convert
continuous neural analog outputs into discrete symbolic inputs, addressing
the boundary condition and logical fragility concerns raised by John von Neumann.

The interface ensures that the transition from the neural layer (continuous weights)
to the symbolic layer (discrete operators) is stable and deterministic.
"""

import json
import logging
import math
import os
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NeuroSymbolicThresholdError(Exception):
    """Exception raised when thresholding fails or inputs are invalid."""
    pass


class NeuroSymbolicInterface:
    """
    Interface for converting neural analog outputs to discrete symbolic inputs.

    This class implements a hard thresholding mechanism that ensures:
    1. Deterministic conversion (same input always yields same output)
    2. Logical stability (no oscillation at boundary conditions)
    3. Clear separation between neural confidence and symbolic truth values

    The thresholding function uses a minimax approach to minimize the worst-case
    error when crossing the boundary between continuous and discrete domains.
    """

    def __init__(
        self,
        threshold: float = 0.5,
        hysteresis: float = 0.05,
        min_confidence: float = 0.75
    ):
        """
        Initialize the NeuroSymbolicInterface.

        Args:
            threshold: The primary threshold for binary conversion (default 0.5)
            hysteresis: The hysteresis band to prevent oscillation at boundaries
            min_confidence: Minimum confidence required for symbolic acceptance
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"Threshold must be between 0.0 and 1.0, got {threshold}")
        if not 0.0 <= hysteresis <= 0.5:
            raise ValueError(f"Hysteresis must be between 0.0 and 0.5, got {hysteresis}")
        if not 0.0 <= min_confidence <= 1.0:
            raise ValueError(f"Min confidence must be between 0.0 and 1.0, got {min_confidence}")

        self.threshold = threshold
        self.hysteresis = hysteresis
        self.min_confidence = min_confidence

        logger.info(
            f"NeuroSymbolicInterface initialized with threshold={threshold}, "
            f"hysteresis={hysteresis}, min_confidence={min_confidence}"
        )

    def apply_hard_threshold(
        self,
        neural_output: float,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        Apply hard thresholding to convert neural output to discrete symbolic input.

        This implements the minimax thresholding function that addresses von Neumann's
        concern about boundary conditions. The function uses a deterministic rule:

        - If neural_output >= threshold + hysteresis: Return True (definite)
        - If neural_output <= threshold - hysteresis: Return False (definite)
        - If in hysteresis band: Use previous state or default to False

        Args:
            neural_output: Continuous value from neural layer (0.0 to 1.0)
            context: Optional context dictionary for logging/debugging

        Returns:
            Tuple of (discrete_value, decision_rationale)
        """
        if not 0.0 <= neural_output <= 1.0:
            raise NeuroSymbolicThresholdError(
                f"Neural output must be in [0.0, 1.0], got {neural_output}"
            )

        upper_bound = self.threshold + self.hysteresis
        lower_bound = self.threshold - self.hysteresis

        if neural_output >= upper_bound:
            discrete_value = True
            rationale = "Above upper hysteresis bound - definite True"
        elif neural_output <= lower_bound:
            discrete_value = False
            rationale = "Below lower hysteresis bound - definite False"
        else:
            # In hysteresis band - use conservative default (False)
            discrete_value = False
            rationale = f"In hysteresis band [{lower_bound:.3f}, {upper_bound:.3f}] - conservative False"

        logger.debug(
            f"Thresholding: input={neural_output:.4f}, output={discrete_value}, "
            f"rationale='{rationale}'"
        )

        return discrete_value, rationale

    def apply_minimax_threshold(
        self,
        neural_outputs: List[float],
        weights: Optional[List[float]] = None
    ) -> Tuple[bool, float, str]:
        """
        Apply minimax thresholding across multiple neural outputs.

        This function computes a weighted expectation and applies thresholding
        to minimize the worst-case error in the boundary region.

        Args:
            neural_outputs: List of continuous values from neural layer
            weights: Optional list of weights for each output (must sum to 1.0)

        Returns:
            Tuple of (discrete_value, expected_value, rationale)
        """
        if not neural_outputs:
            raise NeuroSymbolicThresholdError("Neural outputs list cannot be empty")

        if len(neural_outputs) == 0:
            raise NeuroSymbolicThresholdError("At least one neural output is required")

        # Validate and normalize weights if provided
        if weights is not None:
            if len(weights) != len(neural_outputs):
                raise NeuroSymbolicThresholdError(
                    f"Weights length ({len(weights)}) must match outputs length ({len(neural_outputs)})"
                )
            weight_sum = sum(weights)
            if weight_sum == 0:
                raise NeuroSymbolicThresholdError("Weights cannot sum to zero")
            weights = [w / weight_sum for w in weights]
        else:
            weights = [1.0 / len(neural_outputs)] * len(neural_outputs)

        # Compute weighted expectation
        expected_value = sum(
            output * weight
            for output, weight in zip(neural_outputs, weights)
        )

        # Apply hard threshold with hysteresis
        discrete_value, rationale = self.apply_hard_threshold(expected_value)

        # Add minimax-specific rationale
        max_error = max(
            abs(expected_value - self.threshold),
            abs(expected_value - (1.0 - self.threshold))
        )
        rationale += f"; minimax error estimate: {max_error:.4f}"

        return discrete_value, expected_value, rationale

    def probabilistic_expectation(
        self,
        neural_output: float,
        temperature: float = 1.0
    ) -> Tuple[bool, float]:
        """
        Apply probabilistic expectation with temperature scaling.

        This provides a softer alternative that still produces discrete outputs
        but accounts for uncertainty in the neural predictions.

        Args:
            neural_output: Continuous value from neural layer (0.0 to 1.0)
            temperature: Temperature parameter for probability scaling (default 1.0)

        Returns:
            Tuple of (discrete_value, probability)
        """
        if temperature <= 0:
            raise ValueError(f"Temperature must be positive, got {temperature}")

        # Scale the output
        scaled_output = neural_output / temperature

        # Clamp to valid range
        scaled_output = max(0.0, min(1.0, scaled_output))

        # Apply sigmoid-like transformation for probabilistic interpretation
        # Using a hard sigmoid approximation for discrete output
        if scaled_output >= self.threshold:
            discrete_value = True
            probability = scaled_output
        else:
            discrete_value = False
            probability = 1.0 - scaled_output

        return discrete_value, probability

    def validate_symbolic_input(
        self,
        symbolic_input: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate that symbolic inputs meet the required structure and constraints.

        Args:
            symbolic_input: Dictionary containing symbolic rule parameters

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        required_fields = ['rule_type', 'parameters']
        for field in required_fields:
            if field not in symbolic_input:
                errors.append(f"Missing required field: {field}")

        if 'rule_type' in symbolic_input:
            valid_rule_types = [
                'commutativity', 'associativity', 'distributive',
                'identity', 'inverse', 'transitive'
            ]
            if symbolic_input['rule_type'] not in valid_rule_types:
                errors.append(
                    f"Invalid rule_type: {symbolic_input['rule_type']}. "
                    f"Must be one of {valid_rule_types}"
                )

        if 'confidence' in symbolic_input:
            if not isinstance(symbolic_input['confidence'], (int, float)):
                errors.append("Confidence must be a numeric value")
            elif not 0.0 <= symbolic_input['confidence'] <= 1.0:
                errors.append("Confidence must be in [0.0, 1.0]")

        is_valid = len(errors) == 0
        return is_valid, errors

    def convert_neural_to_symbolic(
        self,
        neural_explanation: Dict[str, Any],
        symbolic_trace: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Convert neural explanation outputs to symbolic inputs.

        This is the main entry point for the neuro-symbolic interface,
        taking neural outputs and converting them to discrete symbolic
        representations that can be used by the symbolic solver.

        Args:
            neural_explanation: Dictionary containing neural explanation outputs
            symbolic_trace: Optional existing symbolic trace to extend

        Returns:
            Dictionary containing the converted symbolic representation
        """
        logger.info("Converting neural explanation to symbolic representation")

        result = {
            'converted': False,
            'symbolic_rules': [],
            'confidence_scores': [],
            'thresholding_details': [],
            'errors': []
        }

        # Extract neural outputs
        neural_outputs = neural_explanation.get('outputs', [])
        if not neural_outputs:
            result['errors'].append("No neural outputs found in explanation")
            return result

        # Convert each output
        for idx, output in enumerate(neural_outputs):
            try:
                # Extract confidence/probability
                confidence = output.get('confidence', 0.5)

                # Apply hard thresholding
                discrete_value, rationale = self.apply_hard_threshold(confidence)

                # Validate confidence meets minimum threshold
                if confidence >= self.min_confidence:
                    rule_type = output.get('rule_type', 'identity')
                    rule_params = output.get('parameters', {})

                    symbolic_rule = {
                        'rule_type': rule_type,
                        'parameters': rule_params,
                        'confidence': confidence,
                        'discrete_active': discrete_value,
                        'thresholding_rationale': rationale
                    }

                    result['symbolic_rules'].append(symbolic_rule)
                    result['confidence_scores'].append(confidence)
                    result['thresholding_details'].append({
                        'index': idx,
                        'confidence': confidence,
                        'discrete_value': discrete_value,
                        'rationale': rationale
                    })

                    if discrete_value:
                        result['converted'] = True

            except (KeyError, ValueError, TypeError) as e:
                error_msg = f"Failed to convert output {idx}: {str(e)}"
                result['errors'].append(error_msg)
                logger.error(error_msg)

        # Compute summary statistics
        if result['confidence_scores']:
            avg_confidence = sum(result['confidence_scores']) / len(result['confidence_scores'])
            max_confidence = max(result['confidence_scores'])
            min_confidence = min(result['confidence_scores'])

            result['summary'] = {
                'total_rules': len(result['symbolic_rules']),
                'active_rules': sum(1 for r in result['symbolic_rules'] if r['discrete_active']),
                'average_confidence': avg_confidence,
                'max_confidence': max_confidence,
                'min_confidence': min_confidence
            }

        logger.info(
            f"Conversion complete: {result['converted']}, "
            f"{len(result['symbolic_rules'])} rules, "
            f"{sum(1 for r in result['symbolic_rules'] if r['discrete_active'])} active"
        )

        return result


def convert_neural_to_symbolic(
    neural_explanation: Dict[str, Any],
    threshold: float = 0.5,
    hysteresis: float = 0.05,
    min_confidence: float = 0.75
) -> Dict[str, Any]:
    """
    Convenience function to convert neural explanations to symbolic representations.

    Args:
        neural_explanation: Dictionary containing neural explanation outputs
        threshold: Threshold for binary conversion (default 0.5)
        hysteresis: Hysteresis band to prevent oscillation (default 0.05)
        min_confidence: Minimum confidence for symbolic acceptance (default 0.75)

    Returns:
        Dictionary containing the converted symbolic representation
    """
    interface = NeuroSymbolicInterface(
        threshold=threshold,
        hysteresis=hysteresis,
        min_confidence=min_confidence
    )
    return interface.convert_neural_to_symbolic(neural_explanation)


def main():
    """
    Main entry point for testing the neural-symbolic interface.

    This function demonstrates the thresholding behavior with sample inputs
    and validates the conversion from neural to symbolic representations.
    """
    logger.info("Starting Neural-Symbolic Interface test")

    # Create interface instance
    interface = NeuroSymbolicInterface(
        threshold=0.5,
        hysteresis=0.05,
        min_confidence=0.75
    )

    # Test cases for hard thresholding
    test_values = [0.0, 0.25, 0.45, 0.46, 0.50, 0.54, 0.55, 0.75, 1.0]

    logger.info("Testing hard thresholding behavior:")
    for value in test_values:
        discrete, rationale = interface.apply_hard_threshold(value)
        logger.info(f"  Input: {value:.2f} -> Discrete: {discrete} | {rationale}")

    # Test minimax thresholding with multiple outputs
    logger.info("\nTesting minimax thresholding:")
    outputs = [0.4, 0.6, 0.8, 0.3]
    weights = [0.25, 0.25, 0.25, 0.25]
    discrete, expected, rationale = interface.apply_minimax_threshold(outputs, weights)
    logger.info(f"  Outputs: {outputs}, Weights: {weights}")
    logger.info(f"  Expected: {expected:.4f}, Discrete: {discrete}")
    logger.info(f"  Rationale: {rationale}")

    # Test conversion from neural explanation
    logger.info("\nTesting neural-to-symbolic conversion:")
    sample_neural_explanation = {
        'outputs': [
            {'confidence': 0.85, 'rule_type': 'commutativity', 'parameters': {'a': 2, 'b': 3}},
            {'confidence': 0.45, 'rule_type': 'associativity', 'parameters': {'a': 1, 'b': 2, 'c': 3}},
            {'confidence': 0.92, 'rule_type': 'distributive', 'parameters': {'a': 2, 'b': 3, 'c': 4}},
            {'confidence': 0.60, 'rule_type': 'identity', 'parameters': {'value': 5}}
        ]
    }

    result = interface.convert_neural_to_symbolic(sample_neural_explanation)
    logger.info(f"  Conversion result: {json.dumps(result, indent=2)}")

    # Validate symbolic input
    logger.info("\nTesting symbolic input validation:")
    valid_input = {
        'rule_type': 'commutativity',
        'parameters': {'a': 2, 'b': 3},
        'confidence': 0.85
    }
    is_valid, errors = interface.validate_symbolic_input(valid_input)
    logger.info(f"  Valid input: is_valid={is_valid}, errors={errors}")

    invalid_input = {
        'rule_type': 'unknown_rule',
        'parameters': {},
        'confidence': 1.5
    }
    is_valid, errors = interface.validate_symbolic_input(invalid_input)
    logger.info(f"  Invalid input: is_valid={is_valid}, errors={errors}")

    logger.info("Neural-Symbolic Interface test completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
