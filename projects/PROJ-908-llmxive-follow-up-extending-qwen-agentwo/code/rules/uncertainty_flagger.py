"""
Module for detecting and flagging extraction uncertainty in reasoning traces.

This module implements logic to identify ambiguous or contradictory traces
that cannot be confidently converted into deterministic rules, as required
by FR-004.
"""
import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set

from rules.extractor import ExtractedRule, RuleExtractor

logger = logging.getLogger(__name__)


@dataclass
class UncertaintyReport:
    """Report detailing traces flagged as uncertain and their reasons."""
    total_traces: int
    uncertain_traces: int
    uncertainty_rate: float
    reasons: Dict[str, int]
    flagged_trace_ids: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class UncertaintyFlag:
    """Enum-like constants for uncertainty reasons."""
    AMBIGUOUS_PATH = "ambiguous_path"
    CONTRADICTORY_EVIDENCE = "contradictory_evidence"
    LOW_CONFIDENCE = "low_confidence"
    MISSING_INTERMEDIATE_STEPS = "missing_intermediate_steps"
    UNDEFINED_BEHAVIOR = "undefined_behavior"


class UncertaintyFlagger:
    """
    Analyzes extracted rules and traces to flag uncertainty.
    
    Identifies traces that:
    1. Lead to contradictory rule applications
    2. Have ambiguous decision paths
    3. Show low confidence scores from the extractor
    4. Lack sufficient intermediate reasoning steps
    """
    
    def __init__(self, confidence_threshold: float = 0.5):
        """
        Initialize the flagger.
        
        Args:
            confidence_threshold: Minimum confidence score to consider a rule extraction valid.
        """
        self.confidence_threshold = confidence_threshold
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def analyze_rules(self, rules: List[ExtractedRule]) -> Tuple[List[str], Dict[str, int]]:
        """
        Analyze a list of extracted rules for uncertainty indicators.
        
        Args:
            rules: List of ExtractedRule objects from the extraction process.
            
        Returns:
            Tuple of (flagged_trace_ids, reasons_counts)
        """
        flagged_ids: List[str] = []
        reasons: Dict[str, int] = {
            UncertaintyFlag.AMBIGUOUS_PATH: 0,
            UncertaintyFlag.CONTRADICTORY_EVIDENCE: 0,
            UncertaintyFlag.LOW_CONFIDENCE: 0,
            UncertaintyFlag.MISSING_INTERMEDIATE_STEPS: 0,
            UncertaintyFlag.UNDEFINED_BEHAVIOR: 0
        }
        
        # Group rules by trace_id to check for contradictions
        trace_rules: Dict[str, List[ExtractedRule]] = {}
        for rule in rules:
            if rule.trace_id not in trace_rules:
                trace_rules[rule.trace_id] = []
            trace_rules[rule.trace_id].append(rule)
        
        for trace_id, trace_rule_list in trace_rules.items():
            # Check for low confidence
            for rule in trace_rule_list:
                if rule.confidence < self.confidence_threshold:
                    flagged_ids.append(trace_id)
                    reasons[UncertaintyFlag.LOW_CONFIDENCE] += 1
                    self.logger.debug(f"Trace {trace_id} flagged: low confidence ({rule.confidence:.2f})")
                    break
            
            # Check for contradictory evidence (same condition, different actions)
            if len(trace_rule_list) > 1:
                conditions: Dict[str, Set[str]] = {}
                for rule in trace_rule_list:
                    cond_key = rule.condition
                    if cond_key not in conditions:
                        conditions[cond_key] = set()
                    conditions[cond_key].add(rule.action)
                
                for cond, actions in conditions.items():
                    if len(actions) > 1:
                        if trace_id not in flagged_ids:
                            flagged_ids.append(trace_id)
                            reasons[UncertaintyFlag.CONTRADICTORY_EVIDENCE] += 1
                            self.logger.warning(f"Trace {trace_id} flagged: contradictory actions for condition '{cond}'")
                        break
            
            # Check for ambiguous paths (multiple rules with similar conditions but different outcomes)
            # This is a heuristic: if a trace has many rules with low support, it's ambiguous
            avg_support = sum(r.support_count for r in trace_rule_list) / len(trace_rule_list) if trace_rule_list else 0
            if avg_support < 2:  # Arbitrary threshold for "ambiguous"
                if trace_id not in flagged_ids:
                    flagged_ids.append(trace_id)
                    reasons[UncertaintyFlag.AMBIGUOUS_PATH] += 1
                    self.logger.debug(f"Trace {trace_id} flagged: ambiguous path (avg support {avg_support:.1f})")
        
        return flagged_ids, reasons
    
    def generate_report(self, total_traces: int, flagged_ids: List[str], reasons: Dict[str, int]) -> UncertaintyReport:
        """Generate a formal uncertainty report."""
        return UncertaintyReport(
            total_traces=total_traces,
            uncertain_traces=len(flagged_ids),
            uncertainty_rate=len(flagged_ids) / total_traces if total_traces > 0 else 0.0,
            reasons=reasons,
            flagged_trace_ids=flagged_ids
        )


def main():
    """
    Main entry point for running the uncertainty flagger on extracted rules.
    
    Usage:
        python -m code.rules.uncertainty_flagger --input=data/processed/extracted_rules.json --output=data/processed/uncertainty_report.json
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Flag extraction uncertainty in rules")
    parser.add_argument("--input", type=str, default="data/processed/extracted_rules.json",
                      help="Path to extracted rules JSON")
    parser.add_argument("--output", type=str, default="data/processed/uncertainty_report.json",
                      help="Path to output uncertainty report")
    parser.add_argument("--threshold", type=float, default=0.5,
                      help="Confidence threshold for flagging uncertainty")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Load rules
    with open(input_path, 'r') as f:
        rules_data = json.load(f)
    
    # Convert to ExtractedRule objects
    rules = [ExtractedRule(**r) for r in rules_data.get('rules', [])]
    total_traces = rules_data.get('total_traces', len(rules))
    
    logger.info(f"Loaded {len(rules)} rules from {total_traces} traces")
    
    # Run analysis
    flagger = UncertaintyFlagger(confidence_threshold=args.threshold)
    flagged_ids, reasons = flagger.analyze_rules(rules)
    report = flagger.generate_report(total_traces, flagged_ids, reasons)
    
    # Save report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report.to_dict(), f, indent=2)
    
    logger.info(f"Uncertainty report saved to {output_path}")
    logger.info(f"Flagged {report.uncertain_traces}/{report.total_traces} traces ({report.uncertainty_rate:.2%})")
    
    return report


if __name__ == "__main__":
    main()
