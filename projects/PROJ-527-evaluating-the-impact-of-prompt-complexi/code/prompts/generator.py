"""
Prompt Generator
=================

This module implements the generation of multiple prompt variants for a
given HumanEval problem.  The variants correspond to five predefined
complexity levels used throughout the project:

* ``simple`` – the raw problem description only.
* ``moderate`` – problem description plus a single illustrative example.
* ``complex`` – problem description plus constraints.
* ``very_complex`` – problem description, constraints and a multi‑step
  instruction set.
* ``degenerate`` – an intentionally verbose / redundant version of the
  prompt.

The implementation is deliberately lightweight and does **not** depend
on any external data beyond the supplied ``HumanEvalProblem`` model.  It
therefore works even when the underlying dataset fields differ slightly
from the original HumanEval schema.

The public API consists of a single function:

``generate_prompt_variants(problem) -> List[PromptVariant]``

which returns a list of ``PromptVariant`` objects – one for each
complexity label.  The function is pure (no I/O) and can be used by the
orchestrator or any downstream storage component.
"""

from __future__ import annotations

from typing import List

from models.data_models import (
    ComplexityLabel,
    HumanEvalProblem,
    PromptVariant,
)

__all__ = ["generate_prompt_variants"]


def _extract_base_prompt(problem: HumanEvalProblem) -> str:
    """
    Extract the core prompt text from a ``HumanEvalProblem`` instance.

    The HumanEval dataset historically stores the problem description in a
    field called ``prompt``.  Some forks rename this attribute to
    ``instruction`` or expose it via dictionary access.  This helper
    attempts a few common patterns and falls back to ``str(problem)`` if
    none are found.

    Parameters
    ----------
    problem: HumanEvalProblem
        The problem for which a prompt should be extracted.

    Returns
    -------
    str
        The raw problem description (no added examples, constraints, etc.).
    """
    # Direct attribute
    if hasattr(problem, "prompt"):
        return getattr(problem, "prompt")
    # Alternate attribute name used by some versions of the dataset
    if hasattr(problem, "instruction"):
        return getattr(problem, "instruction")
    # Dictionary‑like access (e.g. problem["prompt"])
    try:
        return problem["prompt"]  # type: ignore[index]
    except Exception:
        pass
    # Fallback – use the string representation
    return str(problem)


def _make_variant(
    base_prompt: str,
    label: str,
    problem_id: str,
) -> PromptVariant:
    """
    Construct a ``PromptVariant`` instance for a given complexity label.

    The function adds a small, deterministic text fragment that reflects
    the intended complexity level.  The fragments are deliberately simple
    but sufficient for downstream token‑counting and structural‑element
    parsing logic.

    Parameters
    ----------
    base_prompt: str
        The problem description without any extra material.
    label: str
        One of ``simple``, ``moderate``, ``complex``,
        ``very_complex`` or ``degenerate``.
    problem_id: str
        Identifier of the problem (used for traceability).

    Returns
    -------
    PromptVariant
        An instantiated ``PromptVariant`` model.
    """
    # Mapping from label to the extra text that will be appended.
    additions = {
        "moderate": "\nExample:\n# This is a short example illustrating the desired behaviour.",
        "complex": "\nConstraints:\n# • Do not use loops.\n# • Avoid recursion.",
        "very_complex": "\nSteps:\n# 1. Parse the input.\n# 2. Apply the algorithm.\n# 3. Return the result.",
        "degenerate": "\nAdditional notes:\n# This prompt is intentionally verbose and contains redundant information. "
        "The extra sentences do not change the semantics but increase the token count dramatically.",
    }

    # ``simple`` receives the base prompt unchanged.
    if label == "simple":
        full_prompt = base_prompt
    else:
        extra = additions.get(label, "")
        full_prompt = f"{base_prompt}{extra}"

    # Convert the textual label into the appropriate enum member.
    # ``ComplexityLabel`` is expected to be an ``Enum`` whose values are the
    # lower‑case strings used throughout the project.  If the enum does not
    # accept the raw string we fall back to accessing the attribute by name.
    try:
        complexity_enum = ComplexityLabel(label)
    except Exception:
        # Upper‑case attribute access as a secondary strategy.
        complexity_enum = getattr(ComplexityLabel, label.upper())

    # ``PromptVariant`` is a Pydantic model; we initialise it with the
    # fields we know exist.  If the model defines additional required
    # fields they will raise a validation error – this is intentional
    # because it surfaces mismatches early during development.
    return PromptVariant(
        problem_id=problem_id,
        complexity_label=complexity_enum,
        prompt=full_prompt,
    )


def generate_prompt_variants(problem: HumanEvalProblem) -> List[PromptVariant]:
    """
    Generate five prompt variants of differing structural complexity for a
    single HumanEval problem.

    The function returns the variants in a deterministic order matching
    the labels required by the test suite:

    ``['simple', 'moderate', 'complex', 'very_complex', 'degenerate']``

    Parameters
    ----------
    problem: HumanEvalProblem
        The problem for which prompts should be generated.

    Returns
    -------
    List[PromptVariant]
        A list of ``PromptVariant`` objects, one per complexity level.
    """
    base_prompt = _extract_base_prompt(problem)

    # Resolve a stable identifier for the problem.
    # HumanEval problems normally expose an ``task_id`` field; we fall back
    # to ``id`` or ``name`` if necessary.
    if hasattr(problem, "task_id"):
        problem_id = getattr(problem, "task_id")
    elif hasattr(problem, "id"):
        problem_id = getattr(problem, "id")
    elif hasattr(problem, "name"):
        problem_id = getattr(problem, "name")
    else:
        # As a last resort we use the string representation; this ensures
        # the function never crashes due to a missing identifier.
        problem_id = str(problem)

    labels = ["simple", "moderate", "complex", "very_complex", "degenerate"]
    variants: List[PromptVariant] = []

    for label in labels:
        variant = _make_variant(base_prompt, label, problem_id)
        variants.append(variant)

    return variants