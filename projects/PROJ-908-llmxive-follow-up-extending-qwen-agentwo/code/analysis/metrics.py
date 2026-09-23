"""
CoT Quality Metrics Module.

Calculates 'Pattern Reproduction Precision' by comparing extracted rules
against synthetic control traces to verify the ability to reproduce known patterns.
"""

import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from rules.extractor import ExtractedRule, RuleExtractor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class PatternMatch:
    pattern_id: str
    matched_rule_id: Optional[str]
    confidence: float
    is_reproduced: bool


@dataclass
class PatternReproductionResult:
    total_patterns: int
    reproduced_patterns: int
    precision: float
    matches: List[Dict[str, Any]]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def load_synthetic_control_traces(path: Path) -> List[Dict[str, Any]]:
    """
    Load synthetic control traces from JSON file.
    Expects a list of traces, each containing a 'pattern_id' and 'steps'.
    """
    if not path.exists():
        raise FileNotFoundError(f"Synthetic control traces file not found: {path}")

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Expected list of traces in {path}, got {type(data)}")

    logger.info(f"Loaded {len(data)} synthetic control traces from {path}")
    return data


def load_extracted_rules(path: Path) -> List[Dict[str, Any]]:
    """
    Load extracted rules from JSON file.
    """
    if not path.exists():
        raise FileNotFoundError(f"Extracted rules file not found: {path}")

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Expected list of rules in {path}, got {type(data)}")

    logger.info(f"Loaded {len(data)} extracted rules from {path}")
    return data


def extract_pattern_ids_from_traces(traces: List[Dict[str, Any]]) -> Set[str]:
    """
    Extract unique pattern IDs from synthetic control traces.
    """
    pattern_ids = set()
    for trace in traces:
        if 'pattern_id' in trace:
            pattern_ids.add(trace['pattern_id'])
        elif 'metadata' in trace and 'pattern_id' in trace['metadata']:
            pattern_ids.add(trace['metadata']['pattern_id'])
    return pattern_ids


def match_patterns_to_rules(
    traces: List[Dict[str, Any]],
    rules: List[Dict[str, Any]]
) -> List[PatternMatch]:
    """
    Match patterns from traces to extracted rules.
    Returns a list of matches with confidence scores.

    Strategy:
    1. Extract the logical structure of each trace step.
    2. Compare against rule antecedents/consequents.
    3. Assign confidence based on structural similarity.
    """
    matches = []

    # Build a lookup for rules by their logical signature (simplified)
    # In a full ILP implementation, this would use Prolog unification
    rule_signatures = {}
    for rule in rules:
        rule_id = rule.get('id', 'unknown')
        # Create a simple signature from the rule's logical structure
        signature = rule.get('signature', rule.get('logical_form', ''))
        if signature:
            rule_signatures[signature] = rule_id

    for trace in traces:
        pattern_id = trace.get('pattern_id') or trace.get('metadata', {}).get('pattern_id', 'unknown')
        steps = trace.get('steps', [])

        # Analyze trace steps to find matching rules
        best_match = None
        best_confidence = 0.0

        for step in steps:
            # Extract logical form from step
            logical_form = step.get('logical_form', '')
            action = step.get('action', '')
            state = step.get('state', '')

            # Simple heuristic: check if any rule signature matches the step's logical form
            for sig, rule_id in rule_signatures.items():
                # Calculate simple similarity (contains check for now)
                if sig and logical_form and sig in logical_form:
                    confidence = 1.0
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = rule_id
                elif sig and action and sig.split('->')[0].strip() in action:
                    confidence = 0.8
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = rule_id

        matches.append(PatternMatch(
            pattern_id=pattern_id,
            matched_rule_id=best_match,
            confidence=best_confidence,
            is_reproduced=best_confidence >= 0.9  # Threshold for "reproduction"
        ))

    return matches


def calculate_pattern_reproduction_precision(
    traces: List[Dict[str, Any]],
    rules: List[Dict[str, Any]]
) -> PatternReproductionResult:
    """
    Calculate Pattern Reproduction Precision.

    Precision = (Number of patterns successfully reproduced) / (Total number of patterns)

    A pattern is considered reproduced if the extracted rules can match it
    with confidence >= 0.9.
    """
    if not traces:
        logger.warning("No traces provided for pattern reproduction analysis")
        return PatternReproductionResult(
            total_patterns=0,
            reproduced_patterns=0,
            precision=0.0,
            matches=[],
            metadata={"error": "No traces provided"}
        )

    if not rules:
        logger.warning("No rules provided for pattern reproduction analysis")
        return PatternReproductionResult(
            total_patterns=len(traces),
            reproduced_patterns=0,
            precision=0.0,
            matches=[
                PatternMatch(
                    pattern_id=t.get('pattern_id', 'unknown'),
                    matched_rule_id=None,
                    confidence=0.0,
                    is_reproduced=False
                ) for t in traces
            ],
            metadata={"error": "No rules provided"}
        )

    matches = match_patterns_to_rules(traces, rules)
    reproduced_count = sum(1 for m in matches if m.is_reproduced)
    total_patterns = len(matches)
    precision = reproduced_count / total_patterns if total_patterns > 0 else 0.0

    logger.info(f"Pattern Reproduction Precision: {precision:.4f} ({reproduced_count}/{total_patterns})")

    return PatternReproductionResult(
        total_patterns=total_patterns,
        reproduced_patterns=reproduced_count,
        precision=precision,
        matches=[asdict(m) for m in matches],
        metadata={
            "threshold": 0.9,
            "trace_count": len(traces),
            "rule_count": len(rules)
        }
    )


def save_metrics(result: PatternReproductionResult, output_path: Path) -> None:
    """
    Save the metrics result to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result.to_dict(), f, indent=2)

    logger.info(f"Saved metrics to {output_path}")


def main() -> None:
    """
    Main entry point for calculating CoT quality metrics.
    """
    # Default paths
    synthetic_traces_path = Path("data/raw/synthetic_control_traces.json")
    extracted_rules_path = Path("data/processed/extracted_rules.json")
    output_path = Path("data/processed/cot_quality_metrics.json")

    # Allow CLI overrides (simple parsing)
    import sys
    args = sys.argv[1:]
    for arg in args:
        if arg.startswith("--synthetic="):
            synthetic_traces_path = Path(arg.split("=", 1)[1])
        elif arg.startswith("--rules="):
            extracted_rules_path = Path(arg.split("=", 1)[1])
        elif arg.startswith("--output="):
            output_path = Path(arg.split("=", 1)[1])

    logger.info(f"Starting CoT quality metrics calculation")
    logger.info(f"  Synthetic traces: {synthetic_traces_path}")
    logger.info(f"  Extracted rules: {extracted_rules_path}")
    logger.info(f"  Output: {output_path}")

    # Load data
    try:
        traces = load_synthetic_control_traces(synthetic_traces_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise

    try:
        rules = load_extracted_rules(extracted_rules_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise

    # Calculate metrics
    result = calculate_pattern_reproduction_precision(traces, rules)

    # Save results
    save_metrics(result, output_path)

    # Report status
    if result.precision >= 0.95:
        logger.info(f"SUCCESS: Pattern Reproduction Precision ({result.precision:.4f}) meets threshold (>= 0.95)")
    else:
        logger.warning(f"WARNING: Pattern Reproduction Precision ({result.precision:.4f}) below threshold (>= 0.95)")

    return result


if __name__ == "__main__":
    main()
