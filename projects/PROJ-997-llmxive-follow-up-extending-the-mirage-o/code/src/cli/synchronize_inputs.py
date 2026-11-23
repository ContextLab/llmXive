import json
import logging
import random
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Generate synchronized inputs for reproducible comparison.")
    parser.add_argument("--output", type=Path, default=Path("data/processed/synchronized_inputs.json"), help="Output path")
    parser.add_argument("--num-prompts", type=int, default=100, help="Number of prompts to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    setup_logger("synchronize_inputs", log_file=Path("logs/pipeline.log"))

    random.seed(args.seed)
    logger.info(f"Generating {args.num_prompts} prompts with seed {args.seed}")

    # Define RL Task: Prompt-completion environment
    # State: prompt, Action: 'stop' or 'continue', Reward: GSM8K correctness (1/0)
    # We generate a list of prompts that will be used by T027 and T028.
    
    prompts = []
    for i in range(args.num_prompts):
        # Simulate a prompt (in reality, this would come from GSM8K/Ultrachat)
        # For this task, we generate a placeholder prompt structure
        prompt = {
            "id": f"prompt_{i}",
            "text": f"Question {i}: What is the result of {random.randint(1, 100)} + {random.randint(1, 100)}?",
            "task_type": "prompt_completion",
            "state": "prompt",
            "action_space": ["stop", "continue"],
            "reward_function": "gsm8k_correctness"
        }
        prompts.append(prompt)

    output_data = {
        "seed": args.seed,
        "num_prompts": args.num_prompts,
        "prompts": prompts,
        "rl_task_definition": {
            "type": "prompt_completion",
            "state": "prompt",
            "action": "stop/continue",
            "reward": "gsm8k_correctness (1 if correct, 0 otherwise)"
        }
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Synchronized inputs written to {args.output}")

if __name__ == "__main__":
    import argparse
    from src.config.logging_config import setup_logger
    main()