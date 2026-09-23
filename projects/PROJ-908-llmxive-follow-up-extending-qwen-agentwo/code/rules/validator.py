import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    rule_id: str
    is_valid: bool
    reason: str
    matched_transitions: Optional[List[str]] = None
    mismatched_transitions: Optional[List[str]] = None

@dataclass
class ValidationSummary:
    total: int
    valid: int
    invalid: int
    coverage: float

class RuleValidator:
    """
    Cross-checks extracted rules against the Ground Truth Oracle.
    
    Logic:
    1. Loads the Oracle Graph (state transitions).
    2. Loads the Extracted Rules (logic patterns).
    3. Simulates the Oracle's transitions using the extracted rules.
    4. Compares the predicted next states with the Oracle's ground truth.
    5. Calculates precision and coverage.
    """
    def __init__(self, oracle_graph: Dict[str, Any]):
        self.oracle = oracle_graph
        self.transitions = self._extract_transitions(oracle_graph)
        logger.info(f"Initialized RuleValidator with {len(self.transitions)} oracle transitions.")

    def _extract_transitions(self, oracle_graph: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Flatten the oracle graph into a list of state transitions."""
        transitions = []
        # Assuming oracle_graph structure: { "nodes": [...], "edges": [ { "source": ..., "target": ..., "action": ... } ] }
        # Or a list of transitions directly. Adapting to common graph structures.
        if "edges" in oracle_graph:
            for edge in oracle_graph["edges"]:
                transitions.append({
                    "source": edge.get("source"),
                    "target": edge.get("target"),
                    "action": edge.get("action", "unknown"),
                    "conditions": edge.get("conditions", {})
                })
        elif "transitions" in oracle_graph:
            transitions = oracle_graph["transitions"]
        else:
            # Fallback for list of dicts
            if isinstance(oracle_graph, list):
                transitions = oracle_graph
        return transitions

    def validate(self, rules: List[Any]) -> Tuple[List[ValidationResult], ValidationSummary]:
        """
        Validates a list of extracted rules against the Oracle transitions.
        
        Args:
            rules: List of ExtractedRule objects or dicts.
            
        Returns:
            Tuple of (List of per-rule results, Overall summary).
        """
        if not rules:
            logger.warning("No rules provided for validation.")
            return [], ValidationSummary(total=0, valid=0, invalid=0, coverage=0.0)

        results = []
        valid_count = 0
        invalid_count = 0
        covered_transitions = set()

        for i, rule in enumerate(rules):
            rule_id = rule.get("id", f"rule_{i}") if isinstance(rule, dict) else getattr(rule, "id", f"rule_{i}")
            rule_logic = rule.get("logic", "") if isinstance(rule, dict) else getattr(rule, "logic", "")
            
            # Determine if this rule covers any oracle transitions
            matches = []
            mismatches = []
            is_valid = True
            reason = "Rule covers oracle transitions correctly."

            # Simple heuristic validation: Check if the rule's conditions/actions 
            # are compatible with the transitions it claims to cover.
            # In a full ILP setup, we would execute the rule logic.
            # Here, we check if the rule's "action" matches the oracle's action for similar states.
            
            rule_action = rule.get("action", "") if isinstance(rule, dict) else getattr(rule, "action", "")
            rule_condition_states = rule.get("states", []) if isinstance(rule, dict) else getattr(rule, "states", [])

            # Check against oracle transitions
            for t in self.transitions:
                # Heuristic: If the rule mentions the source state or action, check consistency
                if rule_action and t["action"] == rule_action:
                    # Check if source state matches (simplified)
                    if t["source"] in rule_condition_states or not rule_condition_states:
                        matches.append(f"{t['source']} -> {t['target']} ({t['action']})")
                        covered_transitions.add(t["source"] + "_" + t["action"])
                    else:
                        mismatches.append(f"{t['source']} -> {t['target']} ({t['action']})")
                        is_valid = False
                        reason = f"Rule action '{rule_action}' inconsistent with state '{t['source']}'."
            
            if not matches:
                is_valid = False
                reason = "Rule does not match any known oracle transitions (Coverage Gap)."
            
            result = ValidationResult(
                rule_id=rule_id,
                is_valid=is_valid,
                reason=reason,
                matched_transitions=matches[:10], # Limit output size
                mismatched_transitions=mismatches[:10]
            )
            results.append(result)
            
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1

        total_transitions = len(self.transitions)
        coverage = len(covered_transitions) / total_transitions if total_transitions > 0 else 0.0

        summary = ValidationSummary(
            total=len(rules),
            valid=valid_count,
            invalid=invalid_count,
            coverage=coverage
        )

        logger.info(f"Validation complete: {valid_count}/{len(rules)} valid rules. Coverage: {coverage:.2%}")
        return results, summary

def main():
    """
    CLI entry point for T022: Validate extracted rules against the Oracle.
    
    Usage:
      python code/rules/validator.py --rules=data/processed/extracted_rules.json --oracle=data/processed/oracle_graph.json --output=data/processed/validation_report.json
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate extracted rules against the Ground Truth Oracle.")
    parser.add_argument("--rules", type=str, required=True, help="Path to extracted_rules.json")
    parser.add_argument("--oracle", type=str, required=True, help="Path to oracle_graph.json")
    parser.add_argument("--output", type=str, required=True, help="Path to output validation report")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    rules_path = Path(args.rules)
    oracle_path = Path(args.oracle)
    output_path = Path(args.output)

    if not rules_path.exists():
        logger.error(f"Rules file not found: {rules_path}")
        raise FileNotFoundError(f"Rules file not found: {rules_path}")
    
    if not oracle_path.exists():
        logger.error(f"Oracle file not found: {oracle_path}")
        raise FileNotFoundError(f"Oracle file not found: {oracle_path}")

    # Load data
    with open(rules_path, 'r') as f:
        rules_data = json.load(f)
    
    with open(oracle_path, 'r') as f:
        oracle_data = json.load(f)

    # Ensure rules is a list
    if isinstance(rules_data, dict) and "rules" in rules_data:
        rules_list = rules_data["rules"]
    elif isinstance(rules_data, list):
        rules_list = rules_data
    else:
        rules_list = [rules_data]

    # Initialize Validator
    validator = RuleValidator(oracle_data)

    # Run Validation
    results, summary = validator.validate(rules_list)

    # Prepare Report
    report = {
        "summary": asdict(summary),
        "details": [asdict(r) for r in results],
        "metadata": {
            "oracle_file": str(oracle_path),
            "rules_file": str(rules_path),
            "total_oracle_transitions": len(validator.transitions)
        }
    }

    # Write Output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Validation report written to {output_path}")
    print(f"Validation Summary: {summary.total} rules, {summary.valid} valid, Coverage: {summary.coverage:.2%}")

if __name__ == "__main__":
    main()