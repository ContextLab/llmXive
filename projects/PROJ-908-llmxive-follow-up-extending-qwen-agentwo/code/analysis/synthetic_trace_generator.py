import json
import logging
import random
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger("analysis.synthetic_trace_generator")

@dataclass
class CoTStep:
    step_id: int
    thought: str
    action: str
    state: Dict[str, Any]

@dataclass
class SyntheticTrace:
    id: str
    task_id: str
    pattern_id: str
    steps: List[CoTStep]
    metadata: Dict[str, Any]

class SyntheticTraceGenerator:
    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)
        self.patterns = [
            "simple_conjunction",
            "sequential_dependency",
            "conditional_branch"
        ]

    def generate_trace(self, task_id: str, pattern_id: str) -> SyntheticTrace:
        steps = []
        for i in range(5):
            steps.append(CoTStep(
                step_id=i,
                thought=f"Step {i} thought for pattern {pattern_id}",
                action=f"Action {i}",
                state={"step": i, "pattern": pattern_id}
            ))
        return SyntheticTrace(
            id=f"synth_{task_id}_{pattern_id}",
            task_id=task_id,
            pattern_id=pattern_id,
            steps=steps,
            metadata={"generated": True}
        )

def main():
    logger.info("Generating Synthetic Control Traces...")
    output_path = Path("data/raw/synthetic_control_traces.json")
    count = 500
    
    generator = SyntheticTraceGenerator()
    traces = []
    
    for i in range(count):
        pattern = generator.patterns[i % len(generator.patterns)]
        trace = generator.generate_trace(f"task_{i}", pattern)
        traces.append(asdict(trace))
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(traces, f, indent=2)
    
    logger.info(f"Generated {count} synthetic traces. Saved to {output_path}")

if __name__ == "__main__":
    main()
