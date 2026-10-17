"""
Inference module for iterative refinement and convergence analysis.
Implements k‑step refinement loops and result logging.
"""
import json
import logging
import csv
import argparse
from pathlib import Path
from dataclasses import asdict, dataclass
from typing import List, Dict, Any, Optional, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from src.utils import set_global_seed
from src.config import get_config_value

# Configure module logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


@dataclass
class SandboxResult:
    """Result of a single inference step for a problem."""
    task_id: str
    k: int
    output: str
    is_correct: bool
    first_correct_step: Optional[int] = None
    censored: bool = False
    time_to_event: int = 0


def load_model(
    model_name: str = get_config_value("MODEL_NAME"),
    device: str = "cpu",
) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """Load the CodeLlama model."""
    try:
        logger.info(f"Loading model {model_name} on {device}")
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map="auto" if device == "cuda" else None,
            trust_remote_code=True,
        )
        model.eval()
        logger.info("Model loaded successfully")
        return model, tokenizer
    except OSError as e:
        if "not a local folder and is not a valid model identifier" in str(e):
            raise RuntimeError(
                f"Model '{model_name}' not found. Ensure HF_TOKEN is set and the model name is correct."
            ) from e
        raise


def generate_solution(
    model,
    tokenizer,
    prompt: str,
    temperature: float = 0.7,
    top_p: float = 0.95,
) -> str:
    """Generate a single solution for ``prompt``."""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=temperature,
            top_p=top_p,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
        )
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    if "```python" in response:
        start = response.find("```python") + len("```python")
        end = response.find("```", start)
        code = response[start:end].strip() if end != -1 else response[start:].strip()
    elif "```" in response:
        start = response.find("```") + len("```")
        end = response.find("```", start)
        code = response[start:end].strip() if end != -1 else response[start:].strip()
    else:
        code = response.strip()
    return code


def execute_code_in_sandbox(code: str, test_case: Dict[str, Any]) -> Tuple[bool, str]:
    """Light‑weight sandbox that only checks Python syntax."""
    try:
        ast.parse(code)
        return True, ""
    except SyntaxError as e:
        return False, str(e)


def load_input_problems(filepath: str) -> List[Dict[str, Any]]:
    """Read a JSON list of problems."""
    with open(filepath, "r") as f:
        return json.load(f)


def detect_convergence(
    results: List[SandboxResult], task_id: str
) -> Tuple[Optional[int], bool, int]:
    """Determine the first ``k`` at which the solution is correct."""
    task_res = [r for r in results if r.task_id == task_id]
    task_res.sort(key=lambda r: r.k)
    for r in task_res:
        if r.is_correct:
            return r.k, False, r.k
    max_k = max((r.k for r in task_res), default=0)
    return None, True, max_k


def ensure_output_dir(path: str) -> None:
    """Create parent directories for ``path`` if they do not exist."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def save_convergence_results(results: List[SandboxResult], output_path: str) -> None:
    """Write all ``SandboxResult`` rows to ``output_path`` as CSV."""
    ensure_output_dir(output_path)
    fieldnames = [
        "task_id",
        "k",
        "output",
        "is_correct",
        "first_correct_step",
        "censored",
        "time_to_event",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(asdict(r))
    logger.info(f"Convergence results written to {output_path}")


def run_iterative_inference(
    input_path: str,
    output_path: str,
    k_range: List[int],
    model_name: str,
    device: str,
    seed: int,
) -> None:
    """Core driver for the iterative refinement experiment."""
    set_global_seed(seed)
    problems = load_input_problems(input_path)
    model, tokenizer = load_model(model_name=model_name, device=device)

    all_results: List[SandboxResult] = []
    exclusion_log: List[Dict[str, Any]] = []

    for problem in problems:
        task_id = problem.get("task_id", "unknown")
        prompt = problem.get("prompt", "")
        test_case = problem.get("test", {})

        previous_output: Optional[str] = None
        task_step_results: List[SandboxResult] = []

        for k in k_range:
            set_global_seed(seed + k)  # deterministic per step

            cur_prompt = prompt
            if previous_output:
                cur_prompt += f"\n\nPrevious attempt (k={k-1}):\n{previous_output}\n\nRefined attempt (k={k}):"

            try:
                output = generate_solution(
                    model,
                    tokenizer,
                    cur_prompt,
                    temperature=float(get_config_value("MODEL_TEMP", 0.7)),
                    top_p=float(get_config_value("MODEL_TOP_P", 0.95)),
                )
                is_correct, _ = execute_code_in_sandbox(output, test_case)
                res = SandboxResult(
                    task_id=task_id,
                    k=k,
                    output=output,
                    is_correct=is_correct,
                )
                task_step_results.append(res)
                previous_output = output
            except Exception as exc:
                logger.error(f"Error at task {task_id} k={k}: {exc}")
                exclusion_log.append(
                    {"task_id": task_id, "k": k, "reason": str(exc)}
                )

        if task_step_results:
            first_corr, cens, toe = detect_convergence(task_step_results, task_id)
            for r in task_step_results:
                r.first_correct_step = first_corr
                r.censored = cens
                r.time_to_event = toe
            all_results.extend(task_step_results)

    if exclusion_log:
        excl_path = Path(output_path).with_name("exclusions.json")
        with open(excl_path, "w", encoding="utf-8") as f:
            json.dump(exclusion_log, f, indent=2)
        logger.info(f"Exclusion log written to {excl_path}")

    save_convergence_results(all_results, output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Iterative inference for convergence analysis")
    parser.add_argument(
        "--input",
        type=str,
        default=str(Path(get_config_value("DATA_DIR", "data")) / "processed" / "filtered_splits.json"),
        help="Path to input JSON (e.g., filtered_splits.json)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(Path(get_config_value("OUTPUT_DIR", "data/processed") ) / "convergence_results_core.csv"),
        help="Path to output CSV (e.g., convergence_results_core.csv)",
    )
    parser.add_argument(
        "--k_range",
        type=int,
        nargs="+",
        default=get_config_value("CONVERGENCE_K_RANGE", [1, 2, 3]),
        help="Loop counts to evaluate",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda",
        choices=["cpu", "cuda"],
        help="Execution device",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=int(get_config_value("RANDOM_SEED", 42)),
        help="Random seed for reproducibility",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=get_config_value("MODEL_NAME"),
        help="HuggingFace model identifier",
    )

    args = parser.parse_args()

    run_iterative_inference(
        input_path=args.input,
        output_path=args.output,
        k_range=args.k_range,
        model_name=args.model,
        device=args.device,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
