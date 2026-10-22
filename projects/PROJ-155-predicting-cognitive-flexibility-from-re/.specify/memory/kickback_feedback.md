# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 3 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Phase 0 checks that the three *verified* URLs contain both the required HCP resting‑state fMRI time‑series and NIH DCCS scores, but the URLs listed in `research.md` are for diffusion data and chest‑X‑ray datasets, not the needed modalities. Consequently the pipeline will abort before any analysis, meaning the core research question (does RSFC variability predict cognitive flexibility?) cannot be answered with the currently specified data sources. The plan lacks a viable alternative data source or a strategy to obtain appropriate open datasets, rendering the methodological approach unsound.
- The verified source URLs listed for resting‑state fMRI and NIH Toolbox DCCS scores point to diffusion datasets and chest‑X‑ray collections, which do not contain the required high‑dimensional fMRI time‑series or behavioral scores. This makes the cited datasets inappropriate for the research question, violating the requirement that the primary data must provide both RSFC and flexibility measures.
- Principle VII of the constitution sets the default sliding‑window parameters to 30 s. The plan uses a 60 s window and marks the deviation as “PASS (with justified deviation)”. However, the constitution requires any deviation to be justified in the *technical‑design* document, not merely in the plan. No reference to a technical‑design artifact is provided, so the justification is not verifiable against the constitution.
