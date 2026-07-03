"""
Orchestrator for querying LLM with multiple prompt variants per HumanEval problem.

This module implements Task T017: It iterates over HumanEval problems, generates
prompt variants (via generator.py), queries the LLM (via client.py), captures
the generated code, token counts, and structural metadata, and returns a list
of GeneratedCode artifacts.
"""
from __future__ import annotations

import os
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from models.data_models import (
    HumanEvalProblem,
    PromptVariant,
    GeneratedCode,
    ComplexityLabel,
)
from prompts.generator import generate_prompt_variants
from prompts.tokenizer import get_token_count
from llm.client import LLMClient, get_client, LLMClientError
from config import get_project_id, Paths
from utils.logger import get_logger

logger = get_logger(__name__)

def query_variant(
    client: LLMClient,
    variant: PromptVariant,
    problem_id: str,
    timeout: int = 120,
    retry_count: int = 3,
) -> Optional[GeneratedCode]:
    """
    Query the LLM for a single prompt variant and capture the result.

    Args:
        client: The configured LLM client.
        variant: The prompt variant to query.
        problem_id: The ID of the HumanEval problem (for logging/metadata).
        timeout: Request timeout in seconds.
        retry_count: Number of retries on failure.

    Returns:
        A GeneratedCode object if successful, None if all retries fail.
    """
    attempt = 0
    last_error = None

    while attempt < retry_count:
        try:
            logger.info(
                f"Querying LLM for {problem_id} [{variant.complexity_label}] "
                f"(attempt {attempt + 1}/{retry_count})"
            )

            response = client.generate(
                prompt=variant.prompt_text,
                max_tokens=512,
                temperature=0.2,
                timeout=timeout,
            )

            generated_code = response.get("generated_text", "")
            if not generated_code:
                logger.warning(f"Empty response for {problem_id} [{variant.complexity_label}]")
                generated_code = ""

            # Re-count tokens for the generated code to ensure accuracy
            gen_token_count = get_token_count(generated_code)

            return GeneratedCode(
                problem_id=problem_id,
                complexity_label=variant.complexity_label,
                prompt_text=variant.prompt_text,
                prompt_token_count=variant.token_count,
                generated_code=generated_code,
                generated_token_count=gen_token_count,
                structural_element_count=variant.structural_element_count,
                timestamp=datetime.utcnow().isoformat(),
                model_id=client.model_id or "unknown",
                success=True,
                error_message=None,
            )

        except LLMClientError as e:
            last_error = e
            logger.error(f"LLM Client Error for {problem_id}: {e}")
            attempt += 1
            if attempt < retry_count:
                time.sleep(2 ** attempt)  # Exponential backoff
        except Exception as e:
            logger.error(f"Unexpected error querying {problem_id}: {e}", exc_info=True)
            return GeneratedCode(
                problem_id=problem_id,
                complexity_label=variant.complexity_label,
                prompt_text=variant.prompt_text,
                prompt_token_count=variant.token_count,
                generated_code="",
                generated_token_count=0,
                structural_element_count=variant.structural_element_count,
                timestamp=datetime.utcnow().isoformat(),
                model_id=client.model_id or "unknown",
                success=False,
                error_message=str(e),
            )

    # If we exhausted retries
    logger.error(f"Failed to query {problem_id} after {retry_count} attempts: {last_error}")
    return GeneratedCode(
        problem_id=problem_id,
        complexity_label=variant.complexity_label,
        prompt_text=variant.prompt_text,
        prompt_token_count=variant.token_count,
        generated_code="",
        generated_token_count=0,
        structural_element_count=variant.structural_element_count,
        timestamp=datetime.utcnow().isoformat(),
        model_id=client.model_id or "unknown",
        success=False,
        error_message=str(last_error) if last_error else "Max retries exceeded",
    )

def process_problem(
    client: LLMClient,
    problem: HumanEvalProblem,
    skip_labels: Optional[List[ComplexityLabel]] = None,
) -> List[GeneratedCode]:
    """
    Generate prompt variants for a single problem and query the LLM for each.

    Args:
        client: The configured LLM client.
        problem: The HumanEval problem to process.
        skip_labels: Optional list of complexity labels to skip.

    Returns:
        List of GeneratedCode objects for all variants.
    """
    problem_id = problem.task_id
    logger.info(f"Processing problem {problem_id}")

    # Generate variants
    variants = generate_prompt_variants(problem)
    logger.info(f"Generated {len(variants)} variants for {problem_id}")

    results = []
    for variant in variants:
        if skip_labels and variant.complexity_label in skip_labels:
            logger.debug(f"Skipping {variant.complexity_label} for {problem_id}")
            continue

        result = query_variant(client, variant, problem_id)
        if result:
            results.append(result)

    return results

def run_orchestrator(
    problems: List[HumanEvalProblem],
    output_dir: Optional[str] = None,
    skip_labels: Optional[List[ComplexityLabel]] = None,
) -> List[GeneratedCode]:
    """
    Main entry point to run the orchestrator over a list of problems.

    Args:
        problems: List of HumanEvalProblem objects.
        output_dir: Optional directory to write a JSON summary of results.
        skip_labels: Optional list of complexity labels to skip.

    Returns:
        List of all GeneratedCode objects produced.
    """
    project_id = get_project_id()
    logger.info(f"Starting Orchestrator for project {project_id} with {len(problems)} problems")

    client = get_client()
    all_results: List[GeneratedCode] = []

    for problem in problems:
        try:
            problem_results = process_problem(client, problem, skip_labels)
            all_results.extend(problem_results)
        except Exception as e:
            logger.error(f"Critical failure processing {problem.task_id}: {e}", exc_info=True)
            # Continue to next problem rather than failing the whole run

    logger.info(f"Orchestrator complete. Total samples generated: {len(all_results)}")

    if output_dir:
        from pathlib import Path
        from models.data_models import models_to_json
        import json

        out_path = Path(output_dir) / f"{project_id}_orchestrator_results.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(models_to_json(all_results), f, indent=2)
        logger.info(f"Wrote results to {out_path}")

    return all_results

def main():
    """
    CLI entry point for the orchestrator.
    Expects HumanEval data to be available via data.fetcher.load_human_eval().
    """
    from data.fetcher import load_human_eval

    problems = load_human_eval()
    if not problems:
        logger.error("No problems loaded from HumanEval dataset. Exiting.")
        return

    results = run_orchestrator(problems)

    # Quick summary
    success_count = sum(1 for r in results if r.success)
    logger.info(f"Success rate: {success_count}/{len(results)}")

    return results

if __name__ == "__main__":
    main()