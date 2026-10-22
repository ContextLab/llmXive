# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 4 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'science'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- FR‑026’s description of the research question (“Can a generative model learn to accurately simulate the dynamics of complex systems?”) and the associated method (training a recurrent neural network) are unrelated to the core audit of public A/B test summaries. This misalignment means the specified methodology cannot answer the stated research question, violating methodological validity.
- The plan’s Phase 2 I04 references a `source_domain` field for bias handling, but the `ABSummary` entity defined in data-model.md does not include a `source_domain` attribute. This creates a mismatch between the plan (which expects domain information) and the data model (which lacks it). Either add `source_domain` (and related timestamp fields) to the `ABSummary` definition in data-model.md or adjust the plan to compute domain bias using a separate metadata structure.
- Ensure that the synthetic validation dataset’s ground‑truth p‑values and effect sizes are generated with an implementation independent of the reconstruction code used in FR‑003, otherwise the Monte‑Carlo validation may not be truly independent.
- FABRICATED-RESULT signal — projects/PROJ-492-evaluating-the-statistical-validity-of-p/specs/001-evaluating-the-statistical-validity-of-p/spec.md: self-declared fabricated metric — “…thetic_ground_truth.json`. No placeholder values; the count is fixed.  - **T0…”. Research results must be REAL measurements, never simulated / placeholder / hardcoded / drawn from random.*. The reviser must replace this with a genuine computation before the stage advances.
