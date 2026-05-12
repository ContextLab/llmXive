"""Librarian sub-package — search + verify + pdf_sample + expand + cache +
search_trail + theoremsearch + math_classifier.

This module also holds the librarian's package-level shared constants. Per
Constitution Principle I (Single Source of Truth), config values that more
than one consumer needs live here in exactly one canonical place.
"""

from __future__ import annotations

# The default scientific fields the librarian (and the brainstorm/cross-
# domain machinery built around it) operates over. The CLI's per-field
# pipeline pass (``llmxive run`` / ``llmxive brainstorm``) iterates this
# list when no ``--field`` is given, and the cross-domain coverage test
# parametrizes over it — so the two are guaranteed to stay in sync. The
# ``agents/prompts/brainstorm.md`` prose mention of example fields is
# *illustrative only* and intentionally not derived from this constant.
#
# Spec 006 (#113) added ``mathematics`` as the 9th field; #116 collapsed the
# previously-duplicated copies (``cli.py`` + ``tests/phase2/
# test_librarian_cross_domain.py``) into this one.
LIBRARIAN_DEFAULT_FIELDS: tuple[str, ...] = (
    "biology",
    "chemistry",
    "computer science",
    "materials science",
    "mathematics",
    "neuroscience",
    "physics",
    "psychology",
    "statistics",
)

__all__ = ["LIBRARIAN_DEFAULT_FIELDS"]
