import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger("analysis.diverge")

class DivergenceType(Enum):
    MATCH = "Match"
    HALLUCINATION = "Hallucination"
    RULE_GAP = "Rule Gap"
    UNCERTAINTY = "Uncertainty"
    COLD_START = "Cold Start"

@dataclass
class TransitionClassification:
    task_id: str
    step_id: int
    llm_state: str
    oracle_state: str
    classification: str
    confidence: float
    reason: Optional[str] = None

class DivergenceClassifier:
    def __init__(self, oracle_graph: Dict[str, Any], rules: List[Dict[str, Any]]):
        self.oracle_graph = oracle_graph
        self.rules = rules
        self.classifications: List[TransitionClassification] = []

    def classify_transition(self, llm_state: Dict[str, Any], oracle_state: Dict[str, Any], task_id: str, step_id: int) -> TransitionClassification:
        """
        Classify a single transition.
        Logic:
        1. Check if LLM state matches Oracle state exactly -> Match
        2. Check if LLM state matches any extracted Rule -> Match (implied)
        3. If LLM state is valid but not in Oracle -> Rule Gap
        4. If LLM state is invalid/contradictory -> Hallucination
        5. If data is missing/ambiguous -> Uncertainty
        6. If interaction_type is in Oracle but not in Traces -> Cold Start
        """
        # Simplified logic for demonstration of the pipeline structure
        # In reality, this would compare complex state objects
        
        if llm_state == oracle_state:
            classification = DivergenceType.MATCH
            confidence = 1.0
            reason = "States match exactly."
        elif self._is_valid_state(llm_state) and not self._state_in_oracle(llm_state):
            classification = DivergenceType.RULE_GAP
            confidence = 0.8
            reason = "State is valid but not covered by Oracle."
        elif not self._is_valid_state(llm_state):
            classification = DivergenceType.HALLUCINATION
            confidence = 0.9
            reason = "State is invalid or contradictory."
        else:
            classification = DivergenceType.UNCERTAINTY
            confidence = 0.5
            reason = "Ambiguous transition."

        return TransitionClassification(
            task_id=task_id,
            step_id=step_id,
            llm_state=str(llm_state),
            oracle_state=str(oracle_state),
            classification=classification.value,
            confidence=confidence,
            reason=reason
        )

    def _is_valid_state(self, state: Dict[str, Any]) -> bool:
        # Placeholder for validation logic
        return "error" not in str(state).lower()

    def _state_in_oracle(self, state: Dict[str, Any]) -> bool:
        # Placeholder for oracle lookup
        return False

    def classify_batch(self, traces: List[Dict[str, Any]], oracle_data: List[Dict[str, Any]]) -> List[TransitionClassification]:
        """Classify a batch of transitions."""
        results = []
        for i, trace in enumerate(traces):
            if i < len(oracle_data):
                oracle_state = oracle_data[i]
            else:
                oracle_state = {"status": "missing"}
            
            classification = self.classify_transition(
                trace.get("state", {}),
                oracle_state,
                trace.get("task_id", "unknown"),
                trace.get("step_id", i)
            )
            results.append(classification)
        return results

def main():
    logger.info("Starting Divergence Analysis...")
    
    # Load dependencies
    oracle_path = Path("data/processed/oracle_graph.json")
    rules_path = Path("data/processed/extracted_rules.json")
    traces_path = Path("data/raw/cot_traces.json")
    output_path = Path("data/processed/divergence_report.json")
    
    if not oracle_path.exists():
        raise FileNotFoundError(f"Oracle graph not found at {oracle_path}. Run T014 first.")
    if not traces_path.exists():
        raise FileNotFoundError(f"CoT traces not found at {traces_path}. Run T018 first.")
    # Rules are optional for basic divergence, but recommended
    rules = []
    if rules_path.exists():
        with open(rules_path, 'r') as f:
            rules = json.load(f)
    
    with open(oracle_path, 'r') as f:
        oracle_graph = json.load(f)
    
    with open(traces_path, 'r') as f:
        traces = json.load(f)
    
    # Prepare oracle data (simplified extraction from graph)
    oracle_data = []
    for node in oracle_graph.get("nodes", []):
        oracle_data.append(node.get("state_transition", {}))
    
    # Classify
    classifier = DivergenceClassifier(oracle_graph, rules)
    classifications = classifier.classify_batch(traces, oracle_data)
    
    # Aggregate metrics
    counts = {
        "Match": 0,
        "Hallucination": 0,
        "Rule Gap": 0,
        "Uncertainty": 0,
        "Cold Start": 0
    }
    for c in classifications:
        counts[c.classification] += 1
    
    report = {
        "metadata": {
            "total_transitions": len(classifications),
            "source_oracle": str(oracle_path),
            "source_traces": str(traces_path)
        },
        "counts": counts,
        "excluded_metrics": {
            "Uncertainty": counts["Uncertainty"],
            "Cold Start": counts["Cold Start"]
        },
        "classifications": [asdict(c) for c in classifications]
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Divergence report saved to {output_path}")

if __name__ == "__main__":
    main()
