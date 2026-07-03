---
action_items:
- id: 30c503bbbf9f
  severity: science
  text: Report standard deviations or results from multiple seeds for the 'speedup'
    metric in Table 1. Single-run RL results are insufficient to robustly claim consistent
    2-10x speedups across models.
- id: cd324db74da9
  severity: science
  text: Provide quantitative teacher entropy traces (e.g., a plot) for both Qwen and
    Olmo models under the 'No-gate' ablation to substantiate the claim that initial
    entropy differences drive the divergent failure modes.
- id: 3e9571e99afd
  severity: science
  text: Explicitly confirm in the text that all hyperparameters (learning rate, batch
    size, etc.) were identical between the canonical AntiSD runs and the 'No-teacher'
    ablation to rule out optimization instability as a confounder.
artifact_hash: 5a5c1b2fc5b93010078510a2719b14ae8df452ff19cefaab0b0cc9b505e14712
artifact_path: projects/PROJ-611-https-arxiv-org-abs-2605-11609/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T07:25:12.304814Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling theoretical diagnosis of the "shortcut bias" in on-policy self-distillation, supported by a clear derivation linking the per-token signal to conditional Pointwise Mutual Information (PMI). The experimental setup covers a reasonable range of model sizes (4B to 30B) and benchmarks (AIME, HMMT, Minerva), which strengthens the generalizability of the findings. The ablation studies effectively isolate the contributions of the sign reversal, the JSD shape, and the entropy gate.

However, the scientific evidence regarding the robustness of the reported speedups and the stability of the training dynamics requires further quantification. First, Table 1 reports "Speedup" as a single scalar value derived from a "first-reach" step count. In reinforcement learning, training curves are highly stochastic. Without reporting the standard deviation of these step counts across multiple random seeds (or at least multiple runs), it is difficult to assess whether the claimed 2-10x speedup is a consistent phenomenon or a result of favorable initialization in a single run. The lack of error bars on the training dynamics plots (Figure 3) further obscures the variance in convergence behavior.

Second, the ablation study on the entropy gate (Section 4.3) reveals a stark model-dependent behavior: the "No-gate" variant collapses on Qwen models but remains stable on Olmo models. While the authors hypothesize this is due to differences in initial teacher entropy, they do not provide the empirical data (e.g., a plot of median teacher entropy over time for both models under the "No-gate" condition) to substantiate this claim. Without this quantitative evidence, the conclusion that the gate is a "cross-model insurance policy" remains somewhat speculative.

Finally, the "No-teacher" ablation (Section 4.3) demonstrates a collapse attributed to self-reinforcement. To ensure this is not an artifact of optimization instability, the authors must explicitly confirm that all hyperparameters (learning rate, batch size, clip ratios) were held constant between the canonical AntiSD run and the "No-teacher" ablation. If any hyperparameters were tuned for the canonical run but not the ablation, the comparison is confounded.

Addressing these points by adding variance metrics to the speedup claims, providing quantitative entropy traces for the ablation analysis, and confirming hyperparameter consistency in ablations would significantly strengthen the scientific evidence supporting the paper's central claims.
