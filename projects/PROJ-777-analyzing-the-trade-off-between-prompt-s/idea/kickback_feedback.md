# Downstream review concerns (address in this revision)

A downstream convergence panel kicked this project back to the idea stage. You MUST revise the idea — especially the `Methodology sketch` — to RESOLVE each concern below, not merely re-state the idea.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'clarified'; worst unresolved severity = 'science'. Routing to 'flesh_out_in_progress' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The specification requires fitting a Generalized Linear Mixed Model (GLMM) and performing Cochran’s Q test (FR-006, FR-007). The original idea called for a quadratic regression model and a repeated‑measures ANOVA to assess the prompt‑length effect. Introducing GLMM and Cochran’s Q changes the statistical methodology beyond what was proposed, constituting an over‑reach / drift from the intended analysis plan.
- FABRICATED-RESULT signal — projects/PROJ-777-analyzing-the-trade-off-between-prompt-s/specs/001-analyzing-the-trade-off-between-prompt-s/spec.md: self-declared fabricated metric — “…viding a pre‑generated CSV of dummy results (pass@1 scores per token bin…”. Research results must be REAL measurements, never simulated / placeholder / hardcoded / drawn from random.*. The reviser must replace this with a genuine computation before the stage advances.
