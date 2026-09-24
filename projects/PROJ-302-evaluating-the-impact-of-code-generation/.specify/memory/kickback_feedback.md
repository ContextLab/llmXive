# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- T022-SPEC-AMEND proposes modifying `spec.md` to reflect a plan override. This violates the 'Single Source of Truth' (Constitution Principle IV) and standard governance where the Spec is the authority. The Plan's override should be documented in `plan.md` or a design decision record, not by rewriting the Spec artifact itself. The task order implies a dependency on the Spec being mutable by the implementation phase, which is a governance violation.
- T014b-GEN (Context-Based Generation) depends on T012 (GitHub Scraper). However, the task description mentions 'Input: Original code + context'. T012 only fetches metadata and file content. The task should explicitly depend on T014 (Data Acquisition/Preprocessing) or a specific extraction task that prepares the 'context' (e.g., extracting the surrounding code block) to ensure the data flow is complete before generation begins.
