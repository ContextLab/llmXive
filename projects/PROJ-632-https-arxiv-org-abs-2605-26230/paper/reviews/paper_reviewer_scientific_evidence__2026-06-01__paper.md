---
action_items:
- id: 97adae803bd1
  severity: science
  text: Add statistical significance testing (e.g., paired t-tests) for the main quantitative
    results in Tables 1 and 2 to confirm improvements are not due to variance.
- id: b7988d97a9c2
  severity: science
  text: Clarify whether single-view baseline restoration models (Restormer, HI-Diff,
    etc.) were fine-tuned on the specific motion blur distribution used in training
    to ensure a fair comparison.
- id: f209cf4cbe10
  severity: science
  text: Discuss the dependency of the Attention Alignment Loss on ground-truth geometry
    during training and how this impacts real-world deployment where GT is unavailable.
artifact_hash: 1b009a000ce5ea80de9107001816db5f680b271a1e700e1b78677c55727d55dc
artifact_path: projects/PROJ-632-https-arxiv-org-abs-2605-26230/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-01T07:56:29.860740Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: full_revision
---

None of the three prior action items regarding scientific evidence have been adequately addressed in this revision.

1. **Statistical Significance:** Tables 1 and 2 (`tab/pose.tex`, `tab/recon.tex`) still report only mean values without standard deviations or p-values. Without paired t-tests or variance reporting, it is impossible to confirm if improvements are statistically significant or due to random variance. The lack of error bars prevents assessment of reliability, especially given the stochastic nature of diffusion models.

2. **Baseline Fairness:** Section 5.1 (`sec/5_exp.tex`) describes baselines like Restormer and HI-Diff but does not clarify if they were fine-tuned on the specific motion blur distribution used for training GARD. Using off-the-shelf models trained on different degradation distributions would bias the comparison. If Restormer was not adapted to the specific motion blur kernel, its poor performance may reflect domain mismatch rather than architectural superiority.

3. **GT Dependency:** Section 4 (`sec/4_method.tex`) states the Attention Alignment Loss uses target maps $\mathbf{A}^*$ derived from clean multi-view inputs/point clouds. There is no discussion on how this dependency on ground-truth geometry affects training on real-world data where such GT is unavailable, limiting the method's practical applicability. The authors should discuss whether self-supervised alternatives exist or acknowledge this as a limitation for deployment without GT.

These issues undermine the robustness of the empirical claims and require revision before acceptance.
