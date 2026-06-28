---
action_items:
- id: 2115db5e0481
  severity: writing
  text: 'The paper makes strong claims about generalization and system identification
    that are not fully supported by the provided data. Specifically, Section 4.2 claims
    a 9.5% improvement over Explicit Configuration (EXP), but Table tab: unseen in
    the Appendix shows an average absolute improvement of only ~3% (33.75% vs 30.8%
    average). While this may represent a 9.5% *relative* improvement, the phrasing
    "improving the OOD success rate by 9.5%" is ambiguous and risks misleading readers
    into expecting a l'
artifact_hash: 1607b7a56c94fa04d6447f07acdf09cff37e83d8d846355c78db174b7f1d3ac9
artifact_path: projects/PROJ-796-in-context-world-modeling-for-robotic-co/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-28T05:45:09.484383Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes strong claims about generalization and system identification that are not fully supported by the provided data. Specifically, Section 4.2 claims a 9.5% improvement over Explicit Configuration (EXP), but Table `tab: unseen` in the Appendix shows an average absolute improvement of only ~3% (33.75% vs 30.8% average). While this may represent a 9.5% *relative* improvement, the phrasing "improving the OOD success rate by 9.5%" is ambiguous and risks misleading readers into expecting a larger absolute gain. This ambiguity undermines the quantitative rigor of the results.

Additionally, the Abstract states that standard VLAs necessitate "data-intensive fine-tuning for any new environment," implying ICWM avoids this. However, Section 3.1 clarifies ICWM is trained on data collected across "diverse system configurations." This distinction is crucial; ICWM shifts the data burden from test-time to training-time, which should be explicitly acknowledged to avoid misleading readers about the deployment cost. The claim of "zero-shot" adaptation (Appendix A.3) is technically correct regarding test-time updates but glosses over the requirement for diverse training data.

Furthermore, the claim that ICWM "significantly outperforms" baselines (Abstract, Section 4.2) lacks statistical validation. The tables report single success rates without standard deviations or results from multiple random seeds. Without error bars or significance tests, "significant" is an overreach. The t-SNE visualization (Fig 5) suggests representation separation but does not prove the model performs "world modeling" rather than pattern matching on viewpoint features. Finally, the morphological generalization experiments (Section 4.4) test interpolation (70%-100% link lengths) rather than extrapolation to truly novel morphologies. The claim of generalization to "robot morphologies" should be qualified to reflect these specific interpolation bounds.
