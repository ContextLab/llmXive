---
action_items:
- id: 905f3ae498df
  severity: science
  text: Report exact sample size (N) for all evaluation tables (Table 1, Table 2)
    to allow effect size context.
- id: 868a54f88714
  severity: science
  text: Add confidence intervals or significance tests for accuracy comparisons, especially
    for marginal gains (e.g., Table 2 Avg differences).
- id: 20dff5937ce5
  severity: science
  text: Validate the GPT-5.4 judge reliability used in Appendix E (lines 1050+) against
    human gold standards (e.g., Cohen's kappa).
- id: 1b7d5078448b
  severity: science
  text: Confirm data disjointness between training sources (FineVideo/Oops) and evaluation
    benchmarks to rule out leakage.
artifact_hash: e83058c54d1a49095166f0ef2ff7177a4db8d52f3626563ad7ae59fa949315e9
artifact_path: projects/PROJ-610-https-arxiv-org-abs-2605-16403/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-09T10:27:38.054246Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents compelling diagnostic results regarding the "Clever Hans" effect in Video-LLMs but lacks the statistical rigor required to confirm the robustness of the central claims. Table 1 (lines 335-345) reports accuracy percentages for multiple models across interventions, yet does not specify the sample size ($N$) for the evaluation set. Without $N$, effect sizes cannot be contextualized, and confidence intervals are impossible to derive. Similarly, Table 2 (lines 400-425) compares alignment recipes with differences as small as 0.1% (e.g., Avg 62.7 vs 62.8). These marginal gains may fall within statistical noise without error bars or significance testing, making it difficult to distinguish effective recipes from random variance.

A critical concern is the evaluation methodology described in Appendix E (lines 1050+). Free-form model outputs are parsed by GPT-5.4 to generate binary labels for accuracy calculation. No validation of this judge's reliability (e.g., human agreement rate, Cohen's kappa) is provided. If the judge systematically misclassifies nuanced audio descriptions or hallucinations, the reported gains in Table 2 could be artifacts of the evaluation pipeline rather than true model improvements. This introduces a potential confound where the model learns to "game" the judge rather than improve grounding.

Finally, while the "Original" condition serves as a control, the data construction pipeline (Sec 3.1, lines 180-220) involves re-annotating FineVideo. It is unclear if the test set for general benchmarks (Video-MME, etc.) overlaps with the training data derived from FineVideo, risking data leakage that inflates performance metrics. The authors must clarify the disjointness of training and evaluation data to ensure the "alignment tax" analysis is valid.
