"""Reprocessing of externally-ingested papers (spec 024).

A submitted / HuggingFace-ingested paper enters the pipeline BARE at
``Stage.PAPER_INGESTED`` (only ``idea/`` stub + ``paper/{source, metadata.json,
external_resources.md}``) — there is no spec/plan/tasks/draft, and it is a
third-party paper we cannot rewrite. The old behaviour dumped these at
``paper_review`` where the authored-paper revise loop spun forever (124 frozen).

This package triages each ingested paper into the EXISTING pipeline:

- :func:`classify.classify_paper` — does the paper ship runnable code?
- code-included  -> :mod:`branch_code`   (submodule + back-fill spec/plan/tasks
  from the existing code + seed draft from the paper + KEEP original authors ->
  the execution gate decides research_complete vs in_progress).
- no-code        -> :mod:`branch_nocode` (summarise -> extract -> extend into a
  ``brainstormed`` follow-up idea; DROP original authors; cite the original).

:func:`reprocess.reprocess_ingested_paper` is the single entry point the
``PAPER_INGESTED`` graph handler calls.
"""

from __future__ import annotations

__all__ = ["classify_paper", "reprocess_ingested_paper"]


def __getattr__(name: str):  # lazy to avoid importing LLM-heavy branches eagerly
    if name == "classify_paper":
        from llmxive.paper_reprocess.classify import classify_paper

        return classify_paper
    if name == "reprocess_ingested_paper":
        from llmxive.paper_reprocess.reprocess import reprocess_ingested_paper

        return reprocess_ingested_paper
    raise AttributeError(name)
