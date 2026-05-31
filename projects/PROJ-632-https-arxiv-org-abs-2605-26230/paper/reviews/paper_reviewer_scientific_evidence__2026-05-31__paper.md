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
reviewed_at: '2026-05-31T13:11:37.096620Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The manuscript presents GARD, a framework for multi-view 3D reconstruction under degradation. While the empirical results are compelling, the strength of the scientific evidence requires clarification regarding statistical validity, baseline fairness, and training dependencies.

**Sample Size and Replication:**
The evaluation spans five datasets (HiRoom, ETH3D, DTU, 7Scenes, ScanNet++) with $V=10$ views (Sec 5.1, Implementation Details). However, the number of scenes per benchmark is not explicitly stated, making it difficult to assess the effective sample size for statistical power. Furthermore, standard deviations or confidence intervals are absent from Tables 1 and 2 (Pose and Reconstruction). Without statistical significance testing (e.g., paired t-tests across scenes), it is unclear if the reported gains (e.g., Pose AUC30 improvement from 39.20 to 67.22) are robust or influenced by dataset-specific variance.

**Controls and Baselines:**
The comparison against single-view baselines (Restormer, HI-Diff) is potentially confounded by domain mismatch. The paper states baselines are "instantiated using representative single-view image restoration models" (Sec 5.1) but does not explicitly confirm if these models were fine-tuned on the specific synthetic motion blur distribution used for GARD training. If baselines were applied off-the-shelf, the comparison favors GARD due to domain adaptation rather than architectural superiority. The VAE$_\text{MVD}$ baseline is trained specifically for this work, which is a strong control for the representation space hypothesis, but requires confirmation that the VAE encoder capacity matches the DA3 encoder to isolate the *space* variable.

**Robustness to Alternative Explanations:**
The core claim relies on the "Attention Alignment Loss" (Sec 4.2) using target correspondence maps derived from ground-truth point clouds of clean inputs. This supervision signal is unavailable in real-world scenarios where the goal is robustness. The manuscript claims applicability to "real-world observations" (Abstract, Intro), yet the training pipeline depends on synthetic data with known geometry for the alignment loss. This limits the external validity of the robustness claim. Additionally, the reproduction of SIR-Diff (Suppl Sec "Multi-View Restoration") notes missing official code, introducing uncertainty into that specific comparison.

**Recommendations:**
To strengthen the evidence, please include statistical significance tests for the main metrics. Clarify the training protocol for baseline models to ensure domain fairness. Finally, discuss the limitation of the attention alignment loss requiring ground-truth geometry and how the method performs if this component is removed or adapted for unsupervised settings.
