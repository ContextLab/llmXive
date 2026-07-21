"""
Rule Validator: Cross-checks extracted rules against the Ground Truth Oracle.

This module implements the validation logic for FR-002. It loads the extracted
rules from `data/processed/extracted_rules.json` and the Ground Truth Oracle
from `data/processed/oracle_graph.json`. It then evaluates whether the extracted
rules correctly predict state transitions defined in the Oracle.

The validator computes:
- Precision: Fraction of extracted rule predictions that match the Oracle.
- Recall: Fraction of Oracle transitions covered by extracted rules.
- F1 Score: Harmonic mean of Precision and Recall.
- Detailed mismatch logs for debugging.

It outputs a validation report to `data/processed/rule_validation_report.json`.
"""

import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Container for a single rule validation result."""
    rule_id: str
    is_valid: bool
    matched_transitions: int
    total_predicted: int
    oracle_transitions: List[Dict[str, Any]]
    predicted_transitions: List[Dict[str, Any]]
    mismatch_details: List[Dict[str, Any]]
    confidence_score: float

@dataclass
class ValidationSummary:
    """Container for the aggregate validation summary."""
    total_rules: int
    valid_rules: int
    invalid_rules: int
    total_oracle_transitions: int
    total_predicted_transitions: int
    precision: float
    recall: float
    f1_score: float
    validation_results: List[Dict[str, Any]]
    timestamp: str

class RuleValidator:
    """
    Validates extracted rules against the Ground Truth Oracle.

    The validation process involves:
    1. Loading the extracted rules and the oracle graph.
    2. For each extracted rule, simulating its application on relevant states.
    3. Comparing the predicted transitions with the Oracle's ground truth.
    4. Aggregating metrics (Precision, Recall, F1) and generating a report.
    """

    def __init__(self, oracle_path: Path, rules_path: Path):
        """
        Initialize the validator with paths to the Oracle and extracted rules.

        Args:
            oracle_path: Path to the Ground Truth Oracle JSON file.
            rules_path: Path to the Extracted Rules JSON file.
        """
        self.oracle_path = oracle_path
        self.rules_path = rules_path
        self.oracle_graph: Dict[str, Any] = {}
        self.extracted_rules: List[Dict[str, Any]] = []
        self.validation_results: List[ValidationResult] = []

    def load_data(self) -> None:
        """Load the Oracle graph and extracted rules from disk."""
        logger.info(f"Loading Oracle graph from {self.oracle_path}")
        if not self.oracle_path.exists():
            raise FileNotFoundError(f"Oracle file not found: {self.oracle_path}")
        
        with open(self.oracle_path, 'r', encoding='utf-8') as f:
            self.oracle_graph = json.load(f)

        logger.info(f"Loading extracted rules from {self.rules_path}")
        if not self.rules_path.exists():
            raise FileNotFoundError(f"Rules file not found: {self.rules_path}")
        
        with open(self.rules_path, 'r', encoding='utf-8') as f:
            self.extracted_rules = json.load(f)

        logger.info(f"Loaded {len(self.oracle_graph.get('states', []))} states and {len(self.extracted_rules)} rules")

    def _get_oracle_transitions_for_state(self, state_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all valid transitions from a specific state in the Oracle.

        Args:
            state_id: The ID of the state.

        Returns:
            List of transition dictionaries from the Oracle.
        """
        states = self.oracle_graph.get('states', {})
        if state_id not in states:
            return []
        
        state_data = states[state_id]
        transitions = state_data.get('transitions', [])
        return transitions

    def _match_rule_to_states(self, rule: Dict[str, Any]) -> List[str]:
        """
        Identify which states in the Oracle are applicable to a given rule.
        
        This is a simplified matching logic based on rule conditions.
        In a full implementation, this would involve parsing the rule's logical
        conditions (e.g., Prolog predicates) and matching them against state attributes.

        Args:
            rule: The extracted rule dictionary.

        Returns:
            List of state IDs that match the rule's conditions.
        """
        # Simplified logic: Assume rules have a 'condition' field that matches state attributes
        # In a real scenario, this would be more complex (e.g., Prolog query execution)
        matching_states = []
        rule_condition = rule.get('condition', {})
        
        # Example: If rule condition is "location == kitchen", find all states with that location
        # This is a placeholder for actual logical matching logic
        # For now, we iterate through all states and check if they satisfy the condition
        # Note: This is a naive implementation; a real one would use the parser/simulator logic
        
        # Assuming rule conditions are simple key-value pairs for this implementation
        # We will check if the state has the same attributes as the rule condition
        for state_id, state_data in self.oracle_graph.get('states', {}).items():
            state_attrs = state_data.get('attributes', {})
            
            # Check if all rule conditions are met by the state
            match = True
            for key, value in rule_condition.items():
                if state_attrs.get(key) != value:
                    match = False
                    break
            
            if match:
                matching_states.append(state_id)
        
        return matching_states

    def _simulate_rule_application(self, rule: Dict[str, Any], state_id: str) -> List[Dict[str, Any]]:
        """
        Simulate the application of a rule to a state to predict transitions.

        Args:
            rule: The extracted rule.
            state_id: The state to apply the rule to.

        Returns:
            List of predicted transitions based on the rule.
        """
        # Extract the 'effect' or 'action' from the rule
        rule_effect = rule.get('effect', {})
        predicted_transitions = []

        # Create a predicted transition based on the rule's effect
        # This is a simplified simulation; a real one would use the simulator logic
        predicted_transition = {
            "source_state": state_id,
            "action": rule.get('action', 'unknown'),
            "target_state": f"{state_id}_after_{rule.get('action', 'unknown')}",
            "predicted_by_rule": rule.get('rule_id'),
            "details": rule_effect
        }
        
        # Add the predicted transition to the list
        # In a real scenario, we might generate multiple transitions based on the rule
        predicted_transitions.append(predicted_transition)

        return predicted_transitions

    def validate_rule(self, rule: Dict[str, Any]) -> ValidationResult:
        """
        Validate a single extracted rule against the Oracle.

        Args:
            rule: The extracted rule to validate.

        Returns:
            ValidationResult object containing validation details.
        """
        rule_id = rule.get('rule_id', 'unknown')
        logger.info(f"Validating rule: {rule_id}")

        # Find states applicable to this rule
        applicable_states = self._match_rule_to_states(rule)
        
        if not applicable_states:
            logger.warning(f"No applicable states found for rule {rule_id}")
            return ValidationResult(
                rule_id=rule_id,
                is_valid=False,
                matched_transitions=0,
                total_predicted=0,
                oracle_transitions=[],
                predicted_transitions=[],
                mismatch_details=[{"error": "No applicable states"}],
                confidence_score=0.0
            )

        total_predicted = 0
        matched_transitions = 0
        all_predicted = []
        all_oracle = []
        mismatches = []

        for state_id in applicable_states:
            # Get Oracle transitions for this state
            oracle_transitions = self._get_oracle_transitions_for_state(state_id)
            all_oracle.extend(oracle_transitions)

            # Simulate rule application
            predicted_transitions = self._simulate_rule_application(rule, state_id)
            all_predicted.extend(predicted_transitions)
            total_predicted += len(predicted_transitions)

            # Compare predicted vs Oracle
            for pred in predicted_transitions:
                pred_target = pred.get('target_state')
                pred_action = pred.get('action')
                
                # Check if this prediction matches any Oracle transition
                match_found = False
                for oracle_trans in oracle_transitions:
                    if (oracle_trans.get('action') == pred_action and 
                        oracle_trans.get('target_state') == pred_target):
                        match_found = True
                        matched_transitions += 1
                        break
                
                if not match_found:
                    mismatches.append({
                        "state_id": state_id,
                        "predicted": pred,
                        "oracle_options": [t.get('target_state') for t in oracle_transitions]
                    })

        # Calculate confidence score (precision)
        confidence_score = matched_transitions / total_predicted if total_predicted > 0 else 0.0
        is_valid = confidence_score >= 0.95  # Threshold for validity

        return ValidationResult(
            rule_id=rule_id,
            is_valid=is_valid,
            matched_transitions=matched_transitions,
            total_predicted=total_predicted,
            oracle_transitions=all_oracle,
            predicted_transitions=all_predicted,
            mismatch_details=mismatches,
            confidence_score=confidence_score
        )

    def validate_all(self) -> ValidationSummary:
        """
        Validate all extracted rules and compute aggregate metrics.

        Returns:
            ValidationSummary object with aggregate metrics and individual results.
        """
        logger.info("Starting validation of all extracted rules")
        self.validation_results = []
        
        for rule in self.extracted_rules:
            result = self.validate_rule(rule)
            self.validation_results.append(result)

        # Compute aggregate metrics
        total_rules = len(self.validation_results)
        valid_rules = sum(1 for r in self.validation_results if r.is_valid)
        invalid_rules = total_rules - valid_rules

        total_oracle_transitions = sum(len(r.oracle_transitions) for r in self.validation_results)
        total_predicted_transitions = sum(r.total_predicted for r in self.validation_results)
        total_matched = sum(r.matched_transitions for r in self.validation_results)

        precision = total_matched / total_predicted_transitions if total_predicted_transitions > 0 else 0.0
        recall = total_matched / total_oracle_transitions if total_oracle_transitions > 0 else 0.0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        from datetime import datetime
        summary = ValidationSummary(
            total_rules=total_rules,
            valid_rules=valid_rules,
            invalid_rules=invalid_rules,
            total_oracle_transitions=total_oracle_transitions,
            total_predicted_transitions=total_predicted_transitions,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            validation_results=[asdict(r) for r in self.validation_results],
            timestamp=datetime.now().isoformat()
        )

        return summary

    def save_report(self, output_path: Path, summary: ValidationSummary) -> None:
        """
        Save the validation report to a JSON file.

        Args:
            output_path: Path to the output JSON file.
            summary: The ValidationSummary object to save.
        """
        logger.info(f"Saving validation report to {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(summary), f, indent=2, default=str)
        logger.info("Validation report saved successfully")

def main() -> None:
    """Main entry point for the rule validator."""
    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    oracle_path = project_root / 'data' / 'processed' / 'oracle_graph.json'
    rules_path = project_root / 'data' / 'processed' / 'extracted_rules.json'
    output_path = project_root / 'data' / 'processed' / 'rule_validation_report.json'

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize validator
    validator = RuleValidator(oracle_path, rules_path)

    try:
        # Load data
        validator.load_data()

        # Validate all rules
        summary = validator.validate_all()

        # Save report
        validator.save_report(output_path, summary)

        # Log summary
        logger.info(f"Validation Complete: {summary.valid_rules}/{summary.total_rules} rules valid")
        logger.info(f"Precision: {summary.precision:.4f}, Recall: {summary.recall:.4f}, F1: {summary.f1_score:.4f}")

    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise

if __name__ == '__main__':
    main()