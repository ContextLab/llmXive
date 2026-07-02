"""
Orchestrator for querying LLMs with multiple prompt complexity variants.

This module implements the core generation pipeline for User Story 1:
- Iterates over HumanEval problems
- Generates 5 complexity variants per problem (using prompts.generator)
- Queries the LLM client for each variant
- Captures generated code, token counts, and structural metadata
- Returns a list of GeneratedCode objects for downstream processing
"""

import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from project API surface
from models.data_models import (
    HumanEvalProblem,
    PromptVariant,
    GeneratedCode,
    ComplexityLabel,
)
from prompts.generator import generate_prompt_variants
from prompts.tokenizer import count_tokens
from prompts.parser import count_structural_elements
from llm.client import create_client, LLMClient
from utils.logger import get_logger, LLMClientError

logger = get_logger(__name__)

def _create_prompt_variant(
    problem: HumanEvalProblem,
    variant: PromptVariant,
) -> GeneratedCode:
    """
    Query the LLM for a single prompt variant and capture the result.

    Args:
        problem: The original HumanEval problem metadata
        variant: The generated prompt variant with complexity label

    Returns:
        GeneratedCode object containing the LLM response and metadata
    """
    client = create_client()
    prompt_text = variant.prompt_text
    complexity_label = variant.complexity_label

    # Count tokens and structural elements for the prompt
    token_count = count_tokens(prompt_text)
    struct_elements = count_structural_elements(prompt_text)

    logger.info(
        f"Querying LLM for problem {problem.task_id} "
        f"variant {complexity_label} ({token_count} tokens, "
        f"{struct_elements} structural elements)"
    )

    start_time = time.time()
    try:
        response = client.generate(
            prompt=prompt_text,
            max_tokens=1024,
            temperature=0.2,  # Low temperature for code consistency
        )
        elapsed = time.time() - start_time

        generated_code = response.get("code", "")
        finish_reason = response.get("finish_reason", "unknown")

        logger.info(
            f"Received {len(generated_code)} chars from LLM "
            f"in {elapsed:.2f}s (reason: {finish_reason})"
        )

        return GeneratedCode(
            problem_id=problem.task_id,
            problem_description=problem.description,
            complexity_label=complexity_label,
            prompt_text=prompt_text,
            generated_code=generated_code,
            prompt_token_count=token_count,
            structural_element_count=struct_elements["total"],
            generation_time_seconds=elapsed,
            timestamp=datetime.utcnow().isoformat(),
            status="success",
            finish_reason=finish_reason,
        )

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(
            f"LLM query failed for problem {problem.task_id} "
            f"variant {complexity_label}: {str(e)}",
            exc_info=True,
        )
        raise LLMClientError(
            f"Failed to generate code for {problem.task_id} "
            f"{complexity_label}: {str(e)}"
        ) from e

def generate_and_capture(
    problems: List[HumanEvalProblem],
    output_path: Optional[Path] = None,
) -> List[GeneratedCode]:
    """
    Main orchestration function: generate prompts and query LLM for all problems.

    Args:
        problems: List of HumanEvalProblem instances to process
        output_path: Optional path to write intermediate results (not used here,
                    data is returned and written by T018)

    Returns:
        List of GeneratedCode objects with all metadata captured
    """
    logger.info(f"Starting generation for {len(problems)} problems")
    all_results: List[GeneratedCode] = []

    for i, problem in enumerate(problems):
        logger.info(f"Processing problem {i+1}/{len(problems)}: {problem.task_id}")

        # Generate 5 complexity variants for this problem
        variants = generate_prompt_variants(problem)

        if len(variants) != 5:
            logger.warning(
                f"Expected 5 variants for {problem.task_id}, got {len(variants)}"
            )

        # Query LLM for each variant
        for variant in variants:
            try:
                result = _create_prompt_variant(problem, variant)
                all_results.append(result)
            except LLMClientError:
                # Log error but continue with next variant
                # This allows partial progress even if some queries fail
                continue
            except Exception as e:
                logger.error(
                    f"Unexpected error processing {problem.task_id} "
                    f"{variant.complexity_label}: {str(e)}",
                    exc_info=True,
                )
                continue

        # Small delay between problems to avoid rate limiting
        if i < len(problems) - 1:
            time.sleep(0.5)

    logger.info(
        f"Generation complete: {len(all_results)} successful samples "
        f"from {len(problems)} problems"
    )
    return all_results

def main():
    """
    Entry point for running the orchestrator as a script.

    This function:
    1. Loads HumanEval problems from data/processed/humaneval.jsonl (T016)
    2. Calls generate_and_capture to query LLM for all variants
    3. Prints summary statistics to stdout

    Note: Actual storage to parquet is handled by T018 (storage.py)
    """
    from data.fetcher import fetch_humaneval_dataset
    from models.data_models import HumanEvalProblem

    # Load problems
    problems_data = fetch_humaneval_dataset()

    # Convert to HumanEvalProblem objects
    problems = [HumanEvalProblem(**p) for p in problems_data]

    logger.info(f"Loaded {len(problems)} problems from HumanEval dataset")

    # Generate and capture
    results = generate_and_capture(problems)

    # Summary
    success_count = len(results)
    failure_count = len(problems) * 5 - success_count

    print(f"\n=== Generation Summary ===")
    print(f"Problems processed: {len(problems)}")
    print(f"Expected samples: {len(problems) * 5}")
    print(f"Successful captures: {success_count}")
    print(f"Failed captures: {failure_count}")

    # Breakdown by complexity
    by_complexity: Dict[str, int] = {}
    for r in results:
        label = r.complexity_label
        by_complexity[label] = by_complexity.get(label, 0) + 1

    print(f"\nBy complexity level:")
    for label in ["simple", "moderate", "complex", "very_complex", "degenerate"]:
        count = by_complexity.get(label, 0)
        print(f"  {label}: {count}")

    if failure_count > 0:
        print(f"\n⚠️  {failure_count} samples failed. Check logs for details.")

    return results

if __name__ == "__main__":
    main()