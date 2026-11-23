import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("rules.metrics")

@dataclass
class PrecisionResult:
    total_rules: int
    correct_rules: int
    precision: float

def calculate_precision(extracted_rules: List[Dict[str, Any]], oracle_graph: Dict[str, Any]) -> PrecisionResult:
    """
    Calculate the precision of extracted rules against the Oracle.
    A rule is correct if it matches a transition logic in the Oracle.
    
    Matching Logic:
    1. Extract the 'logic' string from the extracted rule.
    2. Normalize both the rule logic and oracle node state_transition strings (lowercase, strip whitespace).
    3. Check if the normalized rule logic is a substring of the normalized state_transition.
    4. Count matches to determine precision.
    """
    if not extracted_rules:
        return PrecisionResult(total_rules=0, correct_rules=0, precision=0.0)

    correct = 0
    total = len(extracted_rules)
    
    # Pre-process oracle nodes for efficient lookup
    oracle_transitions = []
    for node in oracle_graph.get("nodes", []):
        state_trans = node.get("state_transition", {})
        if isinstance(state_trans, dict):
            # Convert dict to string representation
            trans_str = json.dumps(state_trans, sort_keys=True)
        else:
            trans_str = str(state_trans)
        oracle_transitions.append(trans_str.lower().strip())
    
    for rule in extracted_rules:
        logic = str(rule.get("logic", ""))
        if not logic:
            continue
        
        normalized_logic = logic.lower().strip()
        found = False
        
        for trans_str in oracle_transitions:
            if normalized_logic in trans_str:
                found = True
                break
        
        if found:
            correct += 1
        else:
            logger.debug(f"Rule logic not found in oracle: {normalized_logic[:50]}...")
    
    precision = correct / total if total > 0 else 0.0
    return PrecisionResult(total, correct, precision)

def main():
    """
    Main entry point for calculating rule precision.
    Reads extracted rules and oracle graph, calculates precision,
    and writes the result to data/processed/rule_precision.json.
    """
    logger.info("Calculating Rule Precision...")
    
    rules_path = Path("data/processed/extracted_rules.json")
    oracle_path = Path("data/processed/oracle_graph.json")
    output_path = Path("data/processed/rule_precision.json")
    
    # Verify input files exist (fail loudly if missing)
    if not rules_path.exists():
        raise FileNotFoundError(f"Extracted rules not found: {rules_path}. "
                              "Ensure T023 (Rule Extraction) has completed successfully.")
    if not oracle_path.exists():
        raise FileNotFoundError(f"Oracle graph not found: {oracle_path}. "
                              "Ensure T014 (Oracle Generation) has completed successfully.")
    
    # Load extracted rules
    with open(rules_path, 'r') as f:
        rules_data = json.load(f)
        # Handle both list and dict with 'rules' key formats
        if isinstance(rules_data, list):
            rules = rules_data
        elif isinstance(rules_data, dict) and "rules" in rules_data:
            rules = rules_data["rules"]
        else:
            raise ValueError(f"Unexpected format in {rules_path}: expected list or dict with 'rules' key")
    
    # Load oracle graph
    with open(oracle_path, 'r') as f:
        oracle_graph = json.load(f)
    
    # Calculate precision
    result = calculate_precision(rules, oracle_graph)
    
    # Prepare output
    output_data = {
        "precision": result.precision,
        "total_rules": result.total_rules,
        "matching_rules": result.correct_rules
    }
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write output file
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Rule precision calculated: {result.precision:.4f} ({result.correct_rules}/{result.total_rules})")
    logger.info(f"Rule precision saved to {output_path}")

if __name__ == "__main__":
    main()