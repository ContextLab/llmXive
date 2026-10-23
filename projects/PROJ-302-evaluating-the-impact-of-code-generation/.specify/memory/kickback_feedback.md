# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'science'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan relies on a *synthetic review timestamp simulation* (Section 1.1 of research.md) to assign `review_effort_duration` to LLM‑generated PRs. This creates a construct validity problem: the primary outcome for the LLM cohort is not observed but generated from a KDE conditioned on the same covariates used for matching, which can artificially enforce balance and bias the effect estimate toward null. Consequently, the study cannot validly test the causal claim that LLM‑generated code incurs longer review effort than human code.
- The primary outcome `review_effort_duration` for LLM‑generated PRs is *synthetically simulated* (Section 1.1) by sampling from a KDE built on human PRs conditioned on the same five covariates that are later used for propensity‑score matching. This makes the validation target (synthetic review time) a deterministic function of the predictors, creating a circular/tautological validation: the metric being tested is constructed from the very variables used to control for confounding, so any statistical test will at best reflect the simulation procedure rather than real reviewer effort. Consequently the analysis cannot answer the research question “do LLM‑generated code require longer review time?” and violates independence of outcome from predictors.
