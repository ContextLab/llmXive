---
action_items:
- id: 12ae6ee150cf
  severity: science
  text: Specify statistical significance testing methodology (test type, seeds) for
    tables with (*) markers.
- id: 1a991d8d4ac2
  severity: science
  text: Clarify baseline fairness regarding model capacity (2M vs 8B params) and compute
    budget.
- id: a8a5b3848865
  severity: science
  text: Provide exact prompts for Feasibility Oracle to ensure reproducibility and
    check for target leakage.
artifact_hash: 04be55bc6e5d8d960cc49a3798cf6dcfe7112c356a8019a56a3a1b07b8b8ef6d
artifact_path: projects/PROJ-640-https-arxiv-org-abs-2605-28293/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-01T21:53:16.479206Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The scientific evidence supporting ProRL is robust, particularly regarding the ablation of gradient estimators (Sec 5.2.3, `tab:stability`) and the demonstration that the length shortcut is a structural issue (Fig `fig:length-collapse`, Appendix `app:length_collapse`). The cross-evaluator analysis (Sec 5.2, `tab:gru4rec evaluator`) effectively rules out overfitting to the SASRec reward model. The "Rollout@K" analysis (Table `tab:rollout_compact`) provides valuable insight into the latent capacity of the pretrained model.

However, to meet high standards of scientific reproducibility and validity, the following clarifications are required:

1.  **Statistical Rigor**: Tables `tab:overall comparison`, `tab:gru4rec evaluator`, and others mark results as statistically significant (*, p<0.05). However, the methodology for this significance is not described. Please specify the statistical test (e.g., paired t-test, Wilcoxon signed-rank), the number of independent random seeds used for each experiment, and the confidence intervals. Without this, the significance claims are unverifiable.

2.  **Baseline Fairness and Compute**: There is a substantial parameter disparity between ProRL (~2M params, Appendix `app:implementation`) and the LLM-based baselines (Llama-3.1-8B, Appendix `app:baselines`). While ProRL's efficiency is a contribution, the performance gap could be influenced by the LLMs' under-utilization (e.g., 5 epochs vs. ProRL's 50 RL epochs). Please clarify if compute budgets were normalized or if the LLM baselines were given adequate tuning time to reach their potential.

3.  **Data Construction Transparency**: The "Smooth-Guided Data" construction uses a Feasibility Oracle instantiated with GPT-4 (Appendix `app:data_process`, Section "Semantics-based"). This introduces a black-box element that affects reproducibility. Please provide the exact verification prompts used. Additionally, confirm that the target item $i_T$ is excluded from the prompt to prevent information leakage during trajectory mining.

Addressing these points will solidify the empirical claims and ensure the community can accurately reproduce and build upon this work.
