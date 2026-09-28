from __future__ import annotations

import re
from typing import List, Dict, Any, Optional

from models.data_models import (
    HumanEvalProblem,
    PromptVariant,
    StructuralElementCount,
    ComplexityLabel,
)
from prompts.parser import count_structural_elements
from prompts.tokenizer import get_token_count
from utils.logger import get_logger

logger = get_logger(__name__)

# Complexity labels in order of intended complexity
COMPLEXITY_LEVELS = [
    "simple",
    "moderate",
    "complex",
    "very_complex",
    "degenerate",
]

def _build_simple_prompt(problem: HumanEvalProblem) -> str:
    """
    Simple: Problem statement only. No examples, no constraints, no multi-step.
    """
    return f"Implement the following function:\n\n{problem.prompt}"

def _build_moderate_prompt(problem: HumanEvalProblem) -> str:
    """
    Moderate: Problem statement + one illustrative example.
    """
    # Extract a simple example if present, or synthesize one from the problem text
    example_text = ""
    # Try to find an example in the docstring
    if ">>>" in problem.prompt:
        # Take the first example block
        parts = problem.prompt.split(">>>")
        if len(parts) > 1:
            example_part = parts[1].split("\n")[0].strip()
            example_text = f"\n\nExample:\n>>> {example_part}"
    else:
        # Fallback: create a generic example based on function signature
        # This is a heuristic; real HumanEval usually has examples
        func_name_match = re.search(r"def\s+(\w+)\(", problem.prompt)
        if func_name_match:
            func_name = func_name_match.group(1)
            example_text = f"\n\nExample: Call {func_name}(1) and check the result."

    return f"Implement the following function:\n\n{problem.prompt}{example_text}"

def _build_complex_prompt(problem: HumanEvalProblem) -> str:
    """
    Complex: Problem statement + examples + explicit constraints.
    """
    base = _build_moderate_prompt(problem)
    constraints = [
        "Constraint 1: The solution must handle edge cases (e.g., empty inputs, zero values).",
        "Constraint 2: Time complexity should be optimized where possible.",
        "Constraint 3: Do not use external libraries unless specified.",
    ]
    constraints_text = "\n\nConstraints:\n" + "\n".join(constraints)
    return base + constraints_text

def _build_very_complex_prompt(problem: HumanEvalProblem) -> str:
    """
    Very Complex: Problem + examples + constraints + multi-step instructions.
    """
    base = _build_complex_prompt(problem)
    steps = [
        "Step 1: Parse the input requirements and identify the core function signature.",
        "Step 2: Implement the logic to handle the primary use case.",
        "Step 3: Add error handling for edge cases identified in constraints.",
        "Step 4: Verify the solution against the provided examples.",
        "Step 5: Optimize for readability and efficiency.",
    ]
    steps_text = "\n\nInstructions:\n" + "\n".join(steps)
    return base + steps_text

def _build_degenerate_prompt(problem: HumanEvalProblem) -> str:
    """
    Degenerate: Problem + examples + constraints + multi-step + redundant/repetitive text.
    This is designed to have high token count but potentially lower structural utility
    or intentionally confusing redundancy.
    """
    base = _build_very_complex_prompt(problem)
    # Add significant redundancy
    redundancy = [
        "Important Note: Please ensure you follow all instructions carefully.",
        "Reminder: Do not forget to follow all instructions carefully.",
        "Critical: It is vital that you adhere to the instructions carefully.",
        "Warning: Failure to follow instructions carefully will result in errors.",
        "Double Check: Make sure you have followed all instructions carefully.",
        "Triple Check: Verify again that all instructions were followed carefully.",
        "Final Reminder: One last time, follow instructions carefully.",
        "Reiteration: As stated before, follow instructions carefully.",
        "Repetition: To restate, follow instructions carefully.",
        "Emphasis: It cannot be overstated: follow instructions carefully.",
    ]
    # Repeat the redundancy block to inflate token count significantly
    redundancy_block = "\n".join(redundancy * 3)
    return base + "\n\n" + redundancy_block

def generate_prompt_variants(problem: HumanEvalProblem) -> List[PromptVariant]:
    """
    Generate 5 distinct prompt variants for a single HumanEval problem.
    Variants correspond to: simple, moderate, complex, very_complex, degenerate.

    Returns a list of PromptVariant objects with computed metadata.
    """
    logger.info(f"Generating variants for problem {problem.problem_id}")

    builders = {
        "simple": _build_simple_prompt,
        "moderate": _build_moderate_prompt,
        "complex": _build_complex_prompt,
        "very_complex": _build_very_complex_prompt,
        "degenerate": _build_degenerate_prompt,
    }

    variants = []
    for label in COMPLEXITY_LEVELS:
        prompt_text = builders[label](problem)
        token_count = get_token_count(prompt_text)
        structural_counts = count_structural_elements(prompt_text)

        # Calculate dependency depth (simplified: count of sequential steps/instructions)
        # For now, we use a heuristic based on the number of 'Step' or 'Instruction' keywords
        step_count = len(re.findall(r"(?:Step|Instruction)\s*\d+", prompt_text, re.IGNORECASE))
        dependency_depth = max(1, step_count)

        variant = PromptVariant(
            variant_id=f"{problem.problem_id}_{label}",
            problem_id=problem.problem_id,
            complexity_label=label,
            prompt_text=prompt_text,
            token_count=token_count,
            structural_element_count=structural_counts,
            dependency_depth=dependency_depth,
        )
        variants.append(variant)
        logger.debug(
            f"  Variant {label}: tokens={token_count}, "
            f"structure={structural_counts}, depth={dependency_depth}"
        )

    logger.info(f"Generated {len(variants)} variants for {problem.problem_id}")
    return variants

def main():
    """
    Standalone runner to test variant generation on a sample problem.
    """
    from data.loader import load_human_eval_dataset
    from config import Paths

    # Load a small sample for testing
    problems = load_human_eval_dataset(sample_size=1)
    if not problems:
        logger.error("No problems loaded. Exiting.")
        return

    problem = problems[0]
    variants = generate_prompt_variants(problem)

    print(f"Generated {len(variants)} variants for problem {problem.problem_id}:")
    for v in variants:
        print(f"  - {v.complexity_label}: {v.token_count} tokens, "
              f"depth={v.dependency_depth}")

    # Save to a temporary JSON for inspection if needed
    import json
    output_path = Paths.PROCESSED_DIR / "sample_variants.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump([v.model_dump() for v in variants], f, indent=2)
    print(f"Sample variants saved to {output_path}")

if __name__ == "__main__":
    main()
