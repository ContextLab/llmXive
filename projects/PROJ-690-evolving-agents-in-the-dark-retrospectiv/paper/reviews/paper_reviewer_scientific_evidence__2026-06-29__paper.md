---
action_items:
- id: 793e522e70f7
  severity: science
  text: Report confidence intervals or p-values for main results in Table 2 to establish
    statistical significance given test set sizes (100, 59, 100).
- id: 928c7afa944e
  severity: science
  text: Disclose if hyperparameters (k=10, G=3, N=3, theta=0.7) were tuned on the
    test set or provide sensitivity analysis to rule out selection bias.
- id: 926f242a2c12
  severity: science
  text: Provide variance across multiple independent optimization runs (different
    seeds) rather than just candidate variance within a single run (Table 4).
artifact_hash: 1dfb81df34347455cd78b0f836bbc4b7178b6fbb2681f9f18e5c917a00048d5b
artifact_path: projects/PROJ-690-evolving-agents-in-the-dark-retrospectiv/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T18:51:59.126983Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents compelling results, but the scientific evidence lacks statistical rigor required to support the central claims. Table 2 reports pass rates (e.g., 0.59 to 0.78 on SWE-Bench Pro) without confidence intervals or p-values. With test set sizes of 100 (SWE-Bench, GAIA-2) and 59 (Terminal-Bench), these gains require statistical validation to rule out chance, particularly for the smaller Terminal-Bench dataset where a 5% gain could be noise. Table 4 shows variance across candidates within a single run, but not across independent optimization runs with different seeds. This prevents assessing the stability of the method and the reliability of the reported improvements.

Additionally, hyperparameters ($k=10, G=3, N=3, \theta=0.7$) are fixed but not justified as a priori choices (Experiments and Results section). If these were tuned on the test set, this introduces selection bias and inflates the reported effect sizes. The self-preference mechanism (LLM ranking LLM outputs) is not validated against external metrics during optimization, raising concerns about bias amplification where the model optimizes for its own preferences rather than true task success.

To strengthen the evidence, the authors should: (1) report confidence intervals or p-values for the main results in Table 2; (2) disclose if hyperparameters were tuned on the test set or provide a sensitivity analysis; (3) provide variance across multiple independent optimization runs (different seeds) rather than just candidate variance within a run; and (4) validate the self-preference signal against ground truth on a held-out set to ensure it correlates with actual performance. These steps are critical to establish the robustness of the proposed method.
