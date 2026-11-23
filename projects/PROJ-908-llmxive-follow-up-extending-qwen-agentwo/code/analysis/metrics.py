import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("analysis.metrics")

@dataclass
class PatternMatch:
    pattern_id: str
    rule_id: str
    match_type: str
    confidence: float

@dataclass
class PatternReproductionResult:
    total_patterns: int
    matched_patterns: int
    precision: float
    matches: List[PatternMatch]

def load_synthetic_control_traces(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Synthetic control traces not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def load_extracted_rules(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Extracted rules not found: {path}")
    with open(path, 'r') as f:
        data = json.load(f)
        return data.get("rules", [])

def extract_pattern_ids_from_traces(traces: List[Dict[str, Any]]) -> Set[str]:
    patterns = set()
    for trace in traces:
        if "pattern_id" in trace:
            patterns.add(trace["pattern_id"])
    return patterns

def match_patterns_to_rules(patterns: Set[str], rules: List[Dict[str, Any]]) -> List[PatternMatch]:
    matches = []
    for pattern in patterns:
        for rule in rules:
            if pattern in str(rule.get("logic", "")):
                matches.append(PatternMatch(
                    pattern_id=pattern,
                    rule_id=rule.get("id", "unknown"),
                    match_type="exact",
                    confidence=1.0
                ))
                break
    return matches

def calculate_pattern_reproduction_precision(matches: List[PatternMatch], total_patterns: int) -> float:
    if total_patterns == 0:
        return 0.0
    return len(matches) / total_patterns

def save_metrics(result: PatternReproductionResult, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(asdict(result), f, indent=2)

def main():
    logger.info("Calculating Pattern Reproduction Precision...")
    
    traces_path = Path("data/raw/synthetic_control_traces.json")
    rules_path = Path("data/processed/extracted_rules.json")
    output_path = Path("data/processed/synthetic_validation_report.json")
    
    if not traces_path.exists() or not rules_path.exists():
        logger.warning("Required files missing for validation. Skipping.")
        return
    
    traces = load_synthetic_control_traces(traces_path)
    rules = load_extracted_rules(rules_path)
    
    patterns = extract_pattern_ids_from_traces(traces)
    matches = match_patterns_to_rules(patterns, rules)
    precision = calculate_pattern_reproduction_precision(matches, len(patterns))
    
    result = PatternReproductionResult(
        total_patterns=len(patterns),
        matched_patterns=len(matches),
        precision=precision,
        matches=matches
    )
    
    save_metrics(result, output_path)
    logger.info(f"Validation report saved to {output_path}")

if __name__ == "__main__":
    main()
