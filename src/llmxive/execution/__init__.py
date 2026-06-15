"""Analysis-execution stage (spec 023 defect #25).

The implementer writes real code but nothing RAN it, so every project
reached ``research_complete`` as scaffolding — empty ``data/``/``figures/``
and reports full of LLM-written (un-receipted) numbers. This package runs
the project's analysis end-to-end in its per-project venv, using
``quickstart.md`` as the executable run-book, and verifies real artifacts
were produced — gating advancement on them.
"""

from llmxive.execution.analysis_runner import (
    AnalysisRunResult,
    RunCommandResult,
    extract_run_commands,
    run_analysis,
)

__all__ = [
    "AnalysisRunResult",
    "RunCommandResult",
    "extract_run_commands",
    "run_analysis",
]
