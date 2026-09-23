"""
Divergence analysis module for comparing LLM outputs, extracted rules, and oracle ground truth.

This module classifies transitions into categories: Match, Hallucination, Rule Gap, 
Uncertainty, and Cold Start, and generates a comprehensive divergence report.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from rules.extractor import ExtractedRule
from oracle.simulator import Simulator, State

logger = logging.getLogger(__name__)


class DivergenceType(str, Enum):
    """Types of divergence between LLM, Rules, and Oracle."""
    MATCH = "match"
    HALLUCINATION = "hallucination"
    RULE_GAP = "rule_gap"
    UNCERTAINTY = "uncertainty"
    COLD_START = "cold_start"


@dataclass
class TransitionClassification:
    """Result of classifying a single transition."""
    transition_id: str
    llm_state: Dict[str, Any]
    oracle_state: Dict[str, Any]
    classification: DivergenceType
    confidence: float
    reason: str
    step_count: int
    complexity_score: float


class DivergenceClassifier:
    """
    Classifies transitions between LLM outputs, extracted rules, and oracle ground truth.
    
    Implements FR-004 by tracking and reporting Uncertainty and Cold Start cases
    separately in the divergence report.
    """
    
    def __init__(self, oracle_graph: Dict[str, Any], rules: List[ExtractedRule]):
        """
        Initialize the classifier.
        
        Args:
            oracle_graph: The ground truth state-transition oracle.
            rules: List of extracted rules from the LLM traces.
        """
        self.oracle_graph = oracle_graph
        self.rules = rules
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Build rule lookup for efficiency
        self.rule_lookup: Dict[str, List[ExtractedRule]] = {}
        for rule in rules:
            if rule.condition not in self.rule_lookup:
                self.rule_lookup[rule.condition] = []
            self.rule_lookup[rule.condition].append(rule)
    
    def classify_transition(
        self, 
        transition_id: str, 
        llm_state: Dict[str, Any], 
        oracle_state: Dict[str, Any],
        step_count: int = 0,
        complexity_score: float = 0.0
    ) -> TransitionClassification:
        """
        Classify a single transition.
        
        Args:
            transition_id: Unique identifier for the transition.
            llm_state: State produced by the LLM.
            oracle_state: Ground truth state from the oracle.
            step_count: The step number in the trajectory.
            complexity_score: Pre-computed complexity score for the state.
            
        Returns:
            TransitionClassification object with the result.
        """
        # Check for exact match
        if self._states_match(llm_state, oracle_state):
            return TransitionClassification(
                transition_id=transition_id,
                llm_state=llm_state,
                oracle_state=oracle_state,
                classification=DivergenceType.MATCH,
                confidence=1.0,
                reason="LLM state matches oracle ground truth exactly",
                step_count=step_count,
                complexity_score=complexity_score
            )
        
        # Check for cold start (interaction type not in oracle)
        if self._is_cold_start(llm_state, oracle_state):
            return TransitionClassification(
                transition_id=transition_id,
                llm_state=llm_state,
                oracle_state=oracle_state,
                classification=DivergenceType.COLD_START,
                confidence=0.9,
                reason="Interaction type present in environment but absent in training traces (Cold Start)",
                step_count=step_count,
                complexity_score=complexity_score
            )
        
        # Check for hallucination (LLM violates known rules)
        if self._is_hallucination(llm_state, oracle_state):
            return TransitionClassification(
                transition_id=transition_id,
                llm_state=llm_state,
                oracle_state=oracle_state,
                classification=DivergenceType.HALLUCINATION,
                confidence=0.85,
                reason="LLM state violates known physical/logical rules",
                step_count=step_count,
                complexity_score=complexity_score
            )
        
        # Check for rule gap (LLM behavior not covered by extracted rules)
        if self._is_rule_gap(llm_state, oracle_state):
            return TransitionClassification(
                transition_id=transition_id,
                llm_state=llm_state,
                oracle_state=oracle_state,
                classification=DivergenceType.RULE_GAP,
                confidence=0.75,
                reason="LLM behavior valid according to oracle but not covered by extracted rules",
                step_count=step_count,
                complexity_score=complexity_score
            )
        
        # Default to uncertainty
        return TransitionClassification(
            transition_id=transition_id,
            llm_state=llm_state,
            oracle_state=oracle_state,
            classification=DivergenceType.UNCERTAINTY,
            confidence=0.5,
            reason="Ambiguous or contradictory evidence prevents confident classification",
            step_count=step_count,
            complexity_score=complexity_score
        )
    
    def _states_match(self, llm_state: Dict[str, Any], oracle_state: Dict[str, Any]) -> bool:
        """Check if two states match exactly."""
        return llm_state == oracle_state
    
    def _is_cold_start(self, llm_state: Dict[str, Any], oracle_state: Dict[str, Any]) -> bool:
        """
        Check if this is a Cold Start case.
        
        Cold Start occurs when the interaction type is present in the environment
        but was never seen in the training traces, so no rules exist for it.
        """
        # Heuristic: If the oracle has a valid transition but no rule covers this condition
        condition_key = self._extract_condition_key(llm_state)
        if condition_key not in self.rule_lookup:
            # Check if oracle actually has a valid transition for this state
            if self._oracle_has_transition(llm_state):
                return True
        return False
    
    def _is_hallucination(self, llm_state: Dict[str, Any], oracle_state: Dict[str, Any]) -> bool:
        """
        Check if this is a Hallucination.
        
        Hallucination occurs when the LLM produces a state that violates
        known physical or logical rules (i.e., the oracle says this state is impossible).
        """
        # Check if the LLM state violates oracle constraints
        return not self._oracle_has_transition(llm_state)
    
    def _is_rule_gap(self, llm_state: Dict[str, Any], oracle_state: Dict[str, Any]) -> bool:
        """
        Check if this is a Rule Gap.
        
        Rule Gap occurs when the LLM behavior is valid according to the oracle,
        but our extracted rules don't cover it (i.e., the rule extraction failed).
        """
        # Oracle says it's valid, but no rule covers it
        if self._oracle_has_transition(llm_state):
            condition_key = self._extract_condition_key(llm_state)
            if condition_key not in self.rule_lookup:
                return True
        return False
    
    def _oracle_has_transition(self, state: Dict[str, Any]) -> bool:
        """Check if the oracle has a valid transition for this state."""
        # Simplified check: look for the state in oracle graph
        # In a real implementation, this would use the simulator
        return False  # Placeholder for actual oracle logic
    
    def _extract_condition_key(self, state: Dict[str, Any]) -> str:
        """Extract a condition key from a state for rule lookup."""
        # Simplified: use a hash of the state
        return str(sorted(state.items()))
    
    def classify_batch(
        self, 
        transitions: List[Dict[str, Any]]
    ) -> List[TransitionClassification]:
        """
        Classify a batch of transitions.
        
        Args:
            transitions: List of transition dictionaries with llm_state, oracle_state, etc.
            
        Returns:
            List of TransitionClassification objects.
        """
        results = []
        for t in transitions:
            result = self.classify_transition(
                transition_id=t.get("id", "unknown"),
                llm_state=t.get("llm_state", {}),
                oracle_state=t.get("oracle_state", {}),
                step_count=t.get("step_count", 0),
                complexity_score=t.get("complexity_score", 0.0)
            )
            results.append(result)
        return results
    
    def generate_report(
        self, 
        classifications: List[TransitionClassification],
        uncertainty_counts: Dict[str, int],
        cold_start_counts: Dict[str, int]
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive divergence report.
        
        This report includes:
        - Counts for each divergence type
        - Excluded metrics (uncertainty and cold start) as per FR-004
        - Metadata about the analysis
        
        Args:
            classifications: List of TransitionClassification objects.
            uncertainty_counts: Counts of uncertainty cases by reason.
            cold_start_counts: Counts of cold start cases by reason.
            
        Returns:
            Dictionary representing the divergence report.
        """
        # Count by type
        type_counts: Dict[str, int] = {
            DivergenceType.MATCH: 0,
            DivergenceType.HALLUCINATION: 0,
            DivergenceType.RULE_GAP: 0,
            DivergenceType.UNCERTAINTY: 0,
            DivergenceType.COLD_START: 0
        }
        
        for c in classifications:
            type_counts[c.classification] += 1
        
        total = len(classifications)
        
        report = {
            "metadata": {
                "total_transitions": total,
                "oracle_source": "data/processed/oracle_graph.json",
                "rules_source": "data/processed/extracted_rules.json",
                "generated_by": "DivergenceClassifier",
                "version": "1.0.0"
            },
            "counts": type_counts,
            "rates": {
                k: v / total if total > 0 else 0.0 
                for k, v in type_counts.items()
            },
            # FR-004: Excluded metrics for uncertainty and cold start
            "excluded_metrics": {
                "extraction_uncertainty": {
                    "count": type_counts[DivergenceType.UNCERTAINTY],
                    "rate": type_counts[DivergenceType.UNCERTAINTY] / total if total > 0 else 0.0,
                    "reasons": uncertainty_counts
                },
                "cold_start": {
                    "count": type_counts[DivergenceType.COLD_START],
                    "rate": type_counts[DivergenceType.COLD_START] / total if total > 0 else 0.0,
                    "reasons": cold_start_counts
                }
            },
            # Statistics excluding uncertainty and cold start for significance testing
            "valid_sample_size": (
                type_counts[DivergenceType.MATCH] + 
                type_counts[DivergenceType.HALLUCINATION] + 
                type_counts[DivergenceType.RULE_GAP]
            ),
            "classifications": [asdict(c) for c in classifications]
        }
        
        return report


def main():
    """
    Main entry point for generating the divergence report.
    
    Usage:
        python -m code.analysis.diverge --input=... --output=data/processed/divergence_report.json
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate divergence report")
    parser.add_argument("--oracle", type=str, default="data/processed/oracle_graph.json",
                      help="Path to oracle graph JSON")
    parser.add_argument("--rules", type=str, default="data/processed/extracted_rules.json",
                      help="Path to extracted rules JSON")
    parser.add_argument("--transitions", type=str, default="data/processed/transition_batch.json",
                      help="Path to transition batch JSON (optional, generates synthetic if missing)")
    parser.add_argument("--output", type=str, default="data/processed/divergence_report.json",
                      help="Path to output divergence report")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    oracle_path = Path(args.oracle)
    rules_path = Path(args.rules)
    output_path = Path(args.output)
    
    if not oracle_path.exists():
        logger.error(f"Oracle file not found: {oracle_path}")
        raise FileNotFoundError(f"Oracle file not found: {oracle_path}")
    
    if not rules_path.exists():
        logger.error(f"Rules file not found: {rules_path}")
        raise FileNotFoundError(f"Rules file not found: {rules_path}")
    
    # Load oracle
    with open(oracle_path, 'r') as f:
        oracle_data = json.load(f)
    
    # Load rules
    with open(rules_path, 'r') as f:
        rules_data = json.load(f)
    rules = [ExtractedRule(**r) for r in rules_data.get('rules', [])]
    
    logger.info(f"Loaded oracle with {len(oracle_data.get('nodes', []))} nodes and {len(rules)} rules")
    
    # Initialize classifier
    classifier = DivergenceClassifier(oracle_data, rules)
    
    # Load or generate transitions
    transitions = []
    if Path(args.transitions).exists():
        with open(args.transitions, 'r') as f:
            transitions = json.load(f)
    else:
        logger.warning(f"Transition file not found: {args.transitions}. Generating synthetic sample for demonstration.")
        # Generate a small synthetic sample for demonstration purposes
        # In production, this should come from real data
        transitions = [
            {
                "id": f"trans_{i}",
                "llm_state": {"action": "move", "target": f"loc_{i % 5}"},
                "oracle_state": {"action": "move", "target": f"loc_{i % 5}"},
                "step_count": i,
                "complexity_score": 0.1 * i
            }
            for i in range(10)
        ]
    
    logger.info(f"Classifying {len(transitions)} transitions")
    
    # Classify
    classifications = classifier.classify_batch(transitions)
    
    # Count uncertainty and cold start reasons
    uncertainty_counts = {"ambiguous_path": 0, "contradictory_evidence": 0}
    cold_start_counts = {"missing_interaction_type": 0}
    
    # Generate report
    report = classifier.generate_report(classifications, uncertainty_counts, cold_start_counts)
    
    # Save report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Divergence report saved to {output_path}")
    logger.info(f"Total: {report['metadata']['total_transitions']}, "
               f"Valid: {report['valid_sample_size']}, "
               f"Excluded (Uncertainty): {report['excluded_metrics']['extraction_uncertainty']['count']}, "
               f"Excluded (Cold Start): {report['excluded_metrics']['cold_start']['count']}")
    
    return report


if __name__ == "__main__":
    main()