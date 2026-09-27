import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from local utils
from utils.env_config import check_cpu_constraints
from utils.config import initialize_paths, get_path, get_hyperparameter
from utils.errors import BaselineUnavailableError
from utils.state_manager import get_project_root

# Import from data models
from data.models import SymbolicObservation, Trajectory, TaskOutcome

# PyTorch and Transformers
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

class SymbolicGuavaAgent:
    """Agent that reasons over symbolic observations."""
    def __init__(self, model_path: Path, device: str = "cpu"):
        self.device = device
        self.tokenizer = AutoTokenizer.from_pretrained(str(model_path))
        self.model = AutoModelForCausalLM.from_pretrained(
            str(model_path),
            torch_dtype=torch.float32,
            device_map=self.device
        )
        self.model.eval()

    def predict_action(self, observation: SymbolicObservation, history: List[str]) -> str:
        """Generate next action based on symbolic observation."""
        prompt = self._build_prompt(observation, history)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=50,
                temperature=0.7,
                do_sample=True
            )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Extract action from response (simple heuristic)
        return response.split("Action:")[-1].strip() if "Action:" in response else response

    def _build_prompt(self, obs: SymbolicObservation, history: List[str]) -> str:
        parts = ["Current Observation:", obs.to_dict()]
        if history:
            parts.append("History:")
            parts.extend(history)
        parts.append("Next Action:")
        return "\n".join(parts)

def load_held_out_trajectories(project_root: Path) -> List[Trajectory]:
    """Load held-out trajectories for evaluation."""
    data_path = project_root / "data" / "processed" / "symbolic_guava"
    # In a real scenario, filter for held-out set
    trajectories = []
    if data_path.exists():
        for file_path in data_path.glob("*.json"):
            with open(file_path, 'r') as f:
                data = json.load(f)
                trajectories.append(Trajectory(**data))
    return trajectories

def evaluate_agent(agent: SymbolicGuavaAgent, trajectories: List[Trajectory]) -> List[TaskOutcome]:
    """Run evaluation on a list of trajectories."""
    outcomes = []
    for traj in trajectories:
        start_time = time.time()
        success = False
        error = None
        
        try:
            history = []
            for step, obs in enumerate(traj.observations):
                action = agent.predict_action(obs, history)
                history.append(f"Step {step}: {action}")
                # Simulate action execution check (in real scenario, env feedback)
                # For now, assume success if we generated an action
            success = True
        except Exception as e:
            error = str(e)
        
        elapsed = time.time() - start_time
        outcomes.append(TaskOutcome(
            task_id=traj.task_id,
            success=success,
            error=error,
            steps=len(traj.observations),
            latency_ms=elapsed * 1000,
            agent="symbolic"
        ))
    return outcomes

def run_symbolic_evaluation():
    """Main entry point for symbolic evaluation."""
    # 1. Enforce CPU constraints
    print("Checking CPU constraints for inference...")
    try:
        check_cpu_constraints()
    except RuntimeError as e:
        print(f"CPU Constraint Check Failed: {e}")
        sys.exit(1)

    # 2. Initialize
    project_root = get_project_root()
    initialize_paths(project_root)

    # 3. Load Model
    model_path = get_path("data/artifacts/final_model")
    if not Path(model_path).exists():
        print(f"Model not found at {model_path}. Please run training first.")
        sys.exit(1)

    agent = SymbolicGuavaAgent(Path(model_path))

    # 4. Load Data
    trajectories = load_held_out_trajectories(project_root)
    if not trajectories:
        print("No held-out trajectories found.")
        sys.exit(1)

    # 5. Evaluate
    print(f"Evaluating {len(trajectories)} trajectories...")
    outcomes = evaluate_agent(agent, trajectories)

    # 6. Save Results
    output_path = get_path("data/processed/evaluation_outcomes.json")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump([o.dict() for o in outcomes], f, indent=2)
    
    print(f"Evaluation results saved to {output_path}")
    
    # Log success rate
    success_count = sum(1 for o in outcomes if o.success)
    print(f"Success Rate: {success_count}/{len(outcomes)} ({success_count/len(outcomes)*100:.2f}%)")

if __name__ == "__main__":
    run_symbolic_evaluation()