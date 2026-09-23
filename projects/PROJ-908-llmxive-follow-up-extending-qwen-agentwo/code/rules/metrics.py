"""
Metrics calculation for Rule Extraction (User Story 2).

This module implements the calculation of Rule Precision by comparing
extracted rules against the Ground Truth Oracle.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@dataclass
class PrecisionResult:
    """Result container for precision calculation."""
    precision: float
    total_extracted: int
    total_verified: int
    true_positives: int
    false_positives: int
    details: Dict[str, Any]

def _normalize_rule_signature(rule: Dict[str, Any]) -> str:
    """
    Create a canonical string signature for a rule to allow comparison.
    Handles variations in formatting while preserving logical structure.
    """
    rule_type = rule.get("type", "unknown")
    condition = rule.get("condition", "")
    consequence = rule.get("consequence", "")
    
    # Normalize whitespace and sort keys if nested
    def clean(s: str) -> str:
        return " ".join(str(s).split())
    
    return f"{rule_type}:{clean(condition)}->{clean(consequence)}"

def _extract_oracle_rules(oracle_graph: Dict[str, Any]) -> Set[str]:
    """
    Extract a set of normalized rule signatures from the Oracle Graph.
    The Oracle Graph is expected to contain 'nodes' or 'edges' representing
    state transitions and interaction logic.
    """
    rules = set()
    
    # Strategy 1: Look for explicit rules in 'rules' or 'logic' keys
    if "rules" in oracle_graph:
        for r in oracle_graph["rules"]:
            rules.add(_normalize_rule_signature(r))
    
    # Strategy 2: Derive rules from 'edges' (state transitions)
    # Each edge represents a transition: source -> action -> target
    # We treat this as a rule: IF state=source AND action THEN state=target
    if "edges" in oracle_graph:
        for edge in oracle_graph["edges"]:
            source = edge.get("source", "")
            target = edge.get("target", "")
            action = edge.get("action", "")
            if source and target:
                # Construct a synthetic rule signature for the transition
                sig = f"transition:state={source}&action={action}->state={target}"
                rules.add(sig)
    
    # Strategy 3: Look for nodes with 'interaction_logic'
    if "nodes" in oracle_graph:
        for node in oracle_graph["nodes"]:
            logic = node.get("interaction_logic")
            if logic:
                rules.add(_normalize_rule_signature({"type": "interaction", **logic}))

    return rules

def calculate_precision(
    extracted_rules: List[Dict[str, Any]], 
    oracle_graph: Dict[str, Any]
) -> PrecisionResult:
    """
    Calculate Rule Precision by comparing extracted rules against the Oracle.
    
    Precision = True Positives / (True Positives + False Positives)
    
    A True Positive is an extracted rule that matches a rule in the Oracle.
    A False Positive is an extracted rule that does NOT match any Oracle rule.
    (Recall is not calculated here as per task scope, but could be added).
    
    Args:
        extracted_rules: List of rule dictionaries from `data/processed/extracted_rules.json`.
        oracle_graph: Dictionary from `data/processed/oracle_graph.json`.
        
    Returns:
        PrecisionResult containing the scalar precision metric and breakdown.
    """
    if not extracted_rules:
        logger.warning("No extracted rules provided. Precision is 0.0.")
        return PrecisionResult(
            precision=0.0,
            total_extracted=0,
            total_verified=0,
            true_positives=0,
            false_positives=0,
            details={"message": "No extracted rules"}
        )

    oracle_rule_set = _extract_oracle_rules(oracle_graph)
    logger.info(f"Oracle contains {len(oracle_rule_set)} unique rule signatures.")

    true_positives = 0
    false_positives = 0
    matched_rules = []
    unmatched_rules = []

    for rule in extracted_rules:
        sig = _normalize_rule_signature(rule)
        if sig in oracle_rule_set:
            true_positives += 1
            matched_rules.append(sig)
        else:
            false_positives += 1
            unmatched_rules.append(sig)

    total_extracted = len(extracted_rules)
    if total_extracted == 0:
        precision = 0.0
    else:
        precision = true_positives / total_extracted

    logger.info(f"Precision Calculation: TP={true_positives}, FP={false_positives}, Precision={precision:.4f}")

    return PrecisionResult(
        precision=precision,
        total_extracted=total_extracted,
        total_verified=true_positives,
        true_positives=true_positives,
        false_positives=false_positives,
        details={
            "matched_rules": matched_rules[:10], # Limit for log size
            "unmatched_rules": unmatched_rules[:10],
            "oracle_rule_count": len(oracle_rule_set)
        }
    )

def main():
    """
    Entry point to calculate rule precision.
    Reads:
      - data/processed/extracted_rules.json
      - data/processed/oracle_graph.json
    Writes:
      - data/processed/rule_precision.json
    """
    base_path = Path(__file__).resolve().parent.parent.parent
    input_rules_path = base_path / "data" / "processed" / "extracted_rules.json"
    input_oracle_path = base_path / "data" / "processed" / "oracle_graph.json"
    output_path = base_path / "data" / "processed" / "rule_precision.json"

    logger.info(f"Loading extracted rules from {input_rules_path}")
    if not input_rules_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_rules_path}. "
                                "Ensure T023 (Rule Extraction) has completed.")

    logger.info(f"Loading Oracle Graph from {input_oracle_path}")
    if not input_oracle_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_oracle_path}. "
                                "Ensure T014 (Oracle Generation) has completed.")

    with open(input_rules_path, "r", encoding="utf-8") as f:
        extracted_rules = json.load(f)

    with open(input_oracle_path, "r", encoding="utf-8") as f:
        oracle_graph = json.load(f)

    result = calculate_precision(extracted_rules, oracle_graph)

    output_data = {
        "precision": result.precision,
        "total_extracted_rules": result.total_extracted,
        "true_positives": result.true_positives,
        "false_positives": result.false_positives,
        "metrics": {
            "precision": result.precision
        },
        "metadata": {
            "oracle_rule_count": result.details.get("oracle_rule_count", 0),
            "extraction_timestamp": str(Path(input_rules_path).stat().st_mtime),
            "oracle_timestamp": str(Path(input_oracle_path).stat().st_mtime)
        }
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Rule Precision metric saved to {output_path}")
    logger.info(f"Final Precision Score: {result.precision:.4f}")

    return result

if __name__ == "__main__":
    main()
