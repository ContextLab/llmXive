# Revision Specification: Paper Writing Revision — PROJ-652-https-arxiv-org-abs-2606-00408 round 3

**Generated**: 2026-07-16T13:07:05.801495+00:00
**Kind**: paper_writing
**Project**: PROJ-652-https-arxiv-org-abs-2606-00408
**Round**: 3

## Input

Address the following reviewer-raised action items:

- **[auditdef00000] (severity: writing)** Rendering-audit defect (literal_command_text): {"kind": "literal_command_text", "evidence": "he inline \\cite-style citations ((*@\ufffd48\u2020L2-L5\ufffd", "class": "source_fixable", "recommendation": "extend normalize_authors / normalize_refere
- **[auditdef00001] (severity: writing)** Rendering-audit defect (section_number_gap): {"kind": "section_number_gap", "evidence": "expected section 8, saw section 27", "class": "unsupported_construct", "recommendation": "check for stray \\setcounter or \\section* in source", "page": 50}


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 2 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
