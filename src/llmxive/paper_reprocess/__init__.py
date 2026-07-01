"""Reprocessing of externally-ingested papers (spec 024 + 2026-07-01 ethics change).

A submitted / HuggingFace-ingested paper enters the pipeline BARE at
``Stage.PAPER_INGESTED`` (only ``idea/`` stub + ``paper/{source, metadata.json,
external_resources.md}``) — there is no spec/plan/tasks/draft, and it is a
third-party paper we have NO consent to rewrite.

**Ethics invariant (2026-07-01):** an ingested paper's body is never modified and
its original authors are never presented as authors of any llmXive-modified
artifact. Each ingested paper yields exactly two things (design spec
``docs/superpowers/specs/2026-07-01-reviewed-preprints-design.md``):

1. A terminal **Reviewed Preprint** record — review-only, original work
   preserved (:func:`reprocess.reprocess_ingested_paper` marks it;
   :mod:`preprint_review` peer-reviews it once).
2. A **separate** fresh llmXive brainstorm follow-up project — our own study,
   which DROPS the original byline and CITES the original
   (:func:`branch_nocode.spawn_followup_project`).

:func:`reprocess.finalize_reviewed_preprint` orchestrates all three effects
(mark → review → spawn) and is what the ``PAPER_INGESTED`` graph handler calls.
The legacy in-place modify branches (:mod:`branch_code`, :mod:`branch_nocode`'s
``to_followup_idea``) are retired from the intake path — kept only for the
one-time migration of pre-ethics-change projects.
"""

from __future__ import annotations

__all__ = [
    "classify_paper",
    "finalize_reviewed_preprint",
    "reprocess_ingested_paper",
]


def __getattr__(name: str):  # lazy to avoid importing LLM-heavy branches eagerly
    if name == "classify_paper":
        from llmxive.paper_reprocess.classify import classify_paper

        return classify_paper
    if name == "reprocess_ingested_paper":
        from llmxive.paper_reprocess.reprocess import reprocess_ingested_paper

        return reprocess_ingested_paper
    if name == "finalize_reviewed_preprint":
        from llmxive.paper_reprocess.reprocess import finalize_reviewed_preprint

        return finalize_reviewed_preprint
    raise AttributeError(name)
