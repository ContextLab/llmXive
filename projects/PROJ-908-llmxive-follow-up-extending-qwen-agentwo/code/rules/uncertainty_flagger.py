"""
Module: code/rules/uncertainty_flagger.py

Implements logic to flag "Extraction Uncertainty" for ambiguous or contradictory
CoT traces and prepares metrics for exclusion from primary analysis as per FR-004.
"""
import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rules.extractor import ExtractedRule, RuleExtractor
from utils.loaders import load_cot_traces

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class UncertaintyFlag:
    """Represents a flagged uncertainty in a trace."""
    trace_id: str
    reason: str
    confidence_score: float
    type: str  # 'ambiguous', 'contradictory', 'cold_start'


@dataclass
class UncertaintyReport:
    """Report containing flagged uncertainties and exclusion counts."""
    total_traces: int
    flagged_count: int
    flags: List[UncertaintyFlag]
    excluded_metrics: Dict[str, int]
    metadata: Dict[str, Any]


class UncertaintyFlagger:
    """
    Analyzes CoT traces and extracted rules to identify ambiguity and contradiction.
    
    Logic for FR-004:
    - Ambiguous: Trace lacks sufficient detail to derive a unique rule.
    - Contradictory: Trace implies rules that conflict with the Oracle or other traces.
    - Cold Start: No rules could be extracted for a specific task type (coverage gap).
    """

    def __init__(self, oracle_graph_path: str, rules_path: str, traces_path: str):
        self.oracle_path = Path(oracle_graph_path)
        self.rules_path = Path(rules_path)
        self.traces_path = Path(traces_path)
        
        self.oracle_graph: Dict[str, Any] = {}
        self.extracted_rules: List[ExtractedRule] = []
        self.traces: List[Dict[str, Any]] = []

    def load_data(self) -> None:
        """Loads Oracle, Rules, and Traces from disk."""
        logger.info(f"Loading Oracle from {self.oracle_path}")
        with open(self.oracle_path, 'r', encoding='utf-8') as f:
            self.oracle_graph = json.load(f)

        logger.info(f"Loading Extracted Rules from {self.rules_path}")
        with open(self.rules_path, 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
            self.extracted_rules = [ExtractedRule(**r) for r in rules_data.get('rules', [])]

        logger.info(f"Loading CoT Traces from {self.traces_path}")
        self.traces = load_cot_traces(self.traces_path)
        logger.info(f"Loaded {len(self.traces)} traces.")

    def _is_ambiguous(self, trace: Dict[str, Any], extracted_rule: Optional[ExtractedRule]) -> Tuple[bool, str, float]:
        """
        Checks if a trace is ambiguous.
        Ambiguity heuristic: Low confidence in extraction or multiple conflicting rule candidates.
        """
        if not extracted_rule:
            return False, "", 0.0

        # Check confidence score from the extractor (if available in metadata)
        # Assuming the extractor stores a 'confidence' metric in the rule metadata
        confidence = extracted_rule.metadata.get('confidence', 0.0)
        
        # Heuristic: If confidence is below threshold, it's ambiguous
        if confidence < 0.6:
            return True, f"Low extraction confidence ({confidence:.2f})", confidence
        
        # Check for multiple potential rule paths if the extractor supports it
        if len(extracted_rule.possible_rules) > 1:
            return True, f"Multiple rule candidates ({len(extracted_rule.possible_rules)})", confidence

        return False, "", confidence

    def _is_contradictory(self, trace: Dict[str, Any], extracted_rule: Optional[ExtractedRule]) -> Tuple[bool, str, float]:
        """
        Checks if a trace contradicts the Oracle.
        Contradiction: Extracted rule implies a state transition that is explicitly invalid in the Oracle.
        """
        if not extracted_rule:
            return False, "", 0.0

        # Simple check: Does the rule's 'action' exist in the Oracle's valid actions for the given state?
        # This is a simplified check; a full ILP check would be more robust.
        # We assume the oracle_graph has a structure like: { "state_id": { "valid_actions": [...] } }
        
        state_id = trace.get('initial_state_id')
        action = extracted_rule.action

        if state_id and self.oracle_graph:
            state_info = self.oracle_graph.get(state_id, {})
            valid_actions = state_info.get('valid_actions', [])
            
            if valid_actions and action not in valid_actions:
                return True, f"Action '{action}' invalid for state '{state_id}'", 1.0
        
        return False, "", 0.0

    def _check_cold_start(self, task_type: str) -> Tuple[bool, str, float]:
        """
        Checks if a task type has no extracted rules (Coverage Gap).
        """
        # Filter rules by task type
        matching_rules = [r for r in self.extracted_rules if r.task_type == task_type]
        
        if not matching_rules:
            return True, f"No rules extracted for task type '{task_type}'", 1.0
        
        return False, "", 0.0

    def flag_uncertainties(self) -> UncertaintyReport:
        """
        Iterates through traces, applies flagging logic, and aggregates metrics.
        """
        self.load_data()
        
        flags: List[UncertaintyFlag] = []
        cold_start_count = 0
        ambiguity_count = 0
        contradiction_count = 0
        seen_task_types = set()

        for trace in self.traces:
            trace_id = trace.get('id', 'unknown')
            task_type = trace.get('task_type', 'unknown')
            
            # Find corresponding rule (if any)
            # Assuming rules are keyed or searchable by trace_id or task_type
            # For this implementation, we search by task_type as a proxy if trace_id link isn't direct
            # In a real scenario, the extractor would link rules to specific traces.
            # Here we assume a simple mapping or just check existence.
            relevant_rule = None
            for rule in self.extracted_rules:
                if rule.task_type == task_type:
                    relevant_rule = rule
                    break

            # 1. Check Cold Start (Coverage Gap)
            is_cold, reason, conf = self._check_cold_start(task_type)
            if is_cold and task_type not in seen_task_types:
                flags.append(UncertaintyFlag(
                    trace_id=trace_id,
                    reason=reason,
                    confidence_score=conf,
                    type="cold_start"
                ))
                cold_start_count += 1
                seen_task_types.add(task_type) # Count once per type
                continue # If cold start, no rule to check further

            # 2. Check Ambiguity
            is_amb, reason_amb, conf_amb = self._is_ambiguous(trace, relevant_rule)
            if is_amb:
                flags.append(UncertaintyFlag(
                    trace_id=trace_id,
                    reason=reason_amb,
                    confidence_score=conf_amb,
                    type="ambiguous"
                ))
                ambiguity_count += 1
                continue

            # 3. Check Contradiction
            is_con, reason_con, conf_con = self._is_contradictory(trace, relevant_rule)
            if is_con:
                flags.append(UncertaintyFlag(
                    trace_id=trace_id,
                    reason=reason_con,
                    confidence_score=conf_con,
                    type="contradictory"
                ))
                contradiction_count += 1

        excluded_metrics = {
            "extraction_uncertainty": ambiguity_count + contradiction_count,
            "cold_start": cold_start_count
        }

        return UncertaintyReport(
            total_traces=len(self.traces),
            flagged_count=len(flags),
            flags=flags,
            excluded_metrics=excluded_metrics,
            metadata={
                "oracle_path": str(self.oracle_path),
                "rules_path": str(self.rules_path),
                "traces_path": str(self.traces_path)
            }
        )

    def save_report(self, output_path: str) -> None:
        """Saves the uncertainty report to a JSON file."""
        report = self.flag_uncertainties()
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # Convert dataclass to dict for JSON serialization
            data = {
                "total_traces": report.total_traces,
                "flagged_count": report.flagged_count,
                "excluded_metrics": report.excluded_metrics,
                "flags": [asdict(f) for f in report.flags],
                "metadata": report.metadata
            }
            json.dump(data, f, indent=2)
        
        logger.info(f"Uncertainty report saved to {output_path}")
        logger.info(f"Excluded Metrics: {report.excluded_metrics}")


def main():
    """Entry point for running the uncertainty flagger."""
    # Paths relative to project root
    oracle_path = "data/processed/oracle_graph.json"
    rules_path = "data/processed/extracted_rules.json"
    traces_path = "data/raw/cot_traces.json"
    output_path = "data/processed/uncertainty_report.json"

    # Check if input files exist
    if not Path(oracle_path).exists():
        logger.error(f"Oracle file not found: {oracle_path}. Run T014 first.")
        return
    if not Path(rules_path).exists():
        logger.error(f"Rules file not found: {rules_path}. Run T023 first.")
        return
    if not Path(traces_path).exists():
        logger.error(f"Traces file not found: {traces_path}. Run T020 first.")
        return

    flagger = UncertaintyFlagger(oracle_path, rules_path, traces_path)
    flagger.save_report(output_path)
    logger.info("Task T024 completed successfully.")


if __name__ == "__main__":
    main()
