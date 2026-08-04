import csv
import json
import logging
import ast
import os
from typing import List, Dict, Any, Optional, Callable, Tuple
import time
import traceback

from utils.logging import get_logger

logger = get_logger(__name__)


class GenerationError:
    """Container for a policy generation that failed syntax validation."""

    def __init__(self, generation_id: str, seed: int, error_type: str, error_message: str, raw_code: str):
        self.generation_id = generation_id
        self.seed = seed
        self.error_type = error_type
        self.error_message = error_message
        self.raw_code = raw_code

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generation_id": self.generation_id,
            "seed": self.seed,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "raw_code": self.raw_code
        }


class EvolutionaryHarness:
    """
    Orchestrates the evolutionary run of agents on baseline and counterfactual conditions.
    Handles policy execution, complexity analysis, and error tracking.
    """

    def __init__(
        self,
        env_factory: Callable[[], Any],
        policy_generator: Callable[[Dict[str, Any]], str],
        parser_func: Callable[[str], Dict[str, Any]],
        metrics_collector: Optional[Callable[[Any, str], Dict[str, Any]]] = None,
        output_dir: str = "data",
        max_retries: int = 3
    ):
        self.env_factory = env_factory
        self.policy_generator = policy_generator
        self.parser_func = parser_func
        self.metrics_collector = metrics_collector or self._default_metrics_collector
        self.output_dir = output_dir
        self.max_retries = max_retries

        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

        # Tracking for generation errors (T035)
        self.generation_errors: List[GenerationError] = []
        self.successful_runs: List[Dict[str, Any]] = []
        self.logger = logger

    def _default_metrics_collector(self, env: Any, policy_code: str) -> Dict[str, Any]:
        """Default metric collection if none provided."""
        return {
            "total_reward": 0.0,
            "steps": 0,
            "success": False
        }

    def _validate_policy_syntax(self, policy_code: str, generation_id: str, seed: int) -> Tuple[bool, Optional[str]]:
        """
        Validates that the generated policy code is syntactically valid Python.
        Returns (is_valid, error_message).
        """
        try:
            ast.parse(policy_code)
            return True, None
        except SyntaxError as e:
            error_msg = f"SyntaxError at line {e.lineno}: {e.msg}"
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error during syntax check: {str(e)}"
            return False, error_msg

    def _record_generation_error(self, generation_id: str, seed: int, error_type: str, error_message: str, raw_code: str):
        """Records a generation error and logs it."""
        error_obj = GenerationError(generation_id, seed, error_type, error_message, raw_code)
        self.generation_errors.append(error_obj)
        self.logger.warning(
            f"Generation Error recorded [ID: {generation_id}, Seed: {seed}]: "
            f"{error_type} - {error_message}"
        )

    def run_generation(
        self,
        generation_id: str,
        seed: int,
        condition: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Runs a single generation cycle: generate policy -> validate syntax -> run env -> collect metrics.
        Returns metrics dict if successful, None if generation failed.
        """
        self.logger.info(f"Starting generation {generation_id} (Seed: {seed}, Condition: {condition})")

        # 1. Generate Policy Code
        try:
            policy_code = self.policy_generator(context or {})
        except Exception as e:
            self.logger.error(f"Policy generator crashed for {generation_id}: {e}")
            self._record_generation_error(
                generation_id, seed, "generator_crash", str(e), ""
            )
            return None

        # 2. Validate Syntax (T035 Implementation)
        is_valid, error_msg = self._validate_policy_syntax(policy_code, generation_id, seed)
        if not is_valid:
            self._record_generation_error(
                generation_id, seed, "syntax_error", error_msg, policy_code
            )
            return None

        # 3. Parse Complexity (T034 dependency)
        try:
            complexity_metrics = self.parser_func(policy_code)
        except Exception as e:
            # If parsing fails but syntax is valid, it might be a logic error in parsing
            self.logger.warning(f"Complexity parser failed for {generation_id}: {e}")
            complexity_metrics = {"error": str(e)}

        # 4. Run Environment
        env = self.env_factory()
        total_reward = 0.0
        steps = 0
        success = False
        run_error = None

        try:
            obs, info = env.reset(seed=seed)
            done = False
            while not done:
                # Execute policy (simplified execution logic)
                # In a real scenario, this would import/execute the policy code
                action = 0  # Placeholder action
                obs, reward, terminated, truncated, info = env.step(action)
                total_reward += reward
                steps += 1
                done = terminated or truncated
                if steps > 1000: # Safety break
                    break
            success = total_reward > 0.0
        except Exception as e:
            run_error = str(e)
            self.logger.error(f"Environment execution failed for {generation_id}: {e}")

        # 5. Collect Metrics
        metrics = self.metrics_collector(env, policy_code)
        metrics.update({
            "generation_id": generation_id,
            "seed": seed,
            "condition": condition,
            "total_reward": total_reward,
            "steps": steps,
            "success": success,
            "run_error": run_error,
            **complexity_metrics
        })

        self.successful_runs.append(metrics)
        self.logger.info(f"Generation {generation_id} completed successfully.")
        return metrics

    def run_evolution(
        self,
        num_generations: int,
        seeds: List[int],
        conditions: List[str],
        output_filename: str = "evolution_results.csv"
    ) -> str:
        """
        Runs the full evolution process across generations, seeds, and conditions.
        Writes results to CSV and returns the output path.
        """
        all_results = []
        output_path = os.path.join(self.output_dir, output_filename)

        self.logger.info(f"Starting full evolution run: {num_generations} gens, {len(seeds)} seeds, {len(conditions)} conditions")

        gen_idx = 0
        for condition in conditions:
            for seed in seeds:
                for i in range(num_generations):
                    gid = f"gen_{gen_idx:04d}_cond_{condition}_seed_{seed}"
                    result = self.run_generation(gid, seed, condition)
                    if result:
                        all_results.append(result)
                    gen_idx += 1

        # Write successful results to CSV
        if all_results:
            fieldnames = list(all_results[0].keys())
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_results)
            self.logger.info(f"Results written to {output_path}")
        else:
            self.logger.warning("No successful results to write.")

        # Write generation errors to a separate JSON log
        if self.generation_errors:
            error_path = os.path.join(self.output_dir, "generation_errors.json")
            with open(error_path, 'w', encoding='utf-8') as f:
                json.dump([err.to_dict() for err in self.generation_errors], f, indent=2)
            self.logger.info(f"Generation errors logged to {error_path}")

        return output_path

    def get_error_summary(self) -> Dict[str, int]:
        """Returns a summary count of generation errors by type."""
        counts = {}
        for err in self.generation_errors:
            counts[err.error_type] = counts.get(err.error_type, 0) + 1
        return counts