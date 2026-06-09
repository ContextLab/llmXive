---
action_items:
- id: 5027f03c9eae
  severity: science
  text: Report training results averaged over multiple random seeds (e.g., 3-5) with
    standard deviations to support the '2 to 10x speedup' claims in the Abstract and
    Section 4.
- id: e4fe9c36b3cc
  severity: science
  text: Add confidence intervals or statistical significance tests (e.g., t-tests)
    for the accuracy improvements in Table 1 (main_table.tex) to distinguish signal
    from training noise.
artifact_hash: 5a5c1b2fc5b93010078510a2719b14ae8df452ff19cefaab0b0cc9b505e14712
artifact_path: projects/PROJ-611-https-arxiv-org-abs-2605-11609/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-09T21:20:02.307883Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents compelling empirical results across five model sizes and multiple benchmarks, but the scientific evidence lacks necessary statistical rigor to fully support the strong efficiency claims. Section 4 (Experiments) and Table 1 (main_table.tex) report mean accuracy without standard deviations or confidence intervals across training seeds. Reinforcement learning training is inherently stochastic; reporting single-run results (implied by the absence of error bars) makes the claim that AntiSD reaches GRPO accuracy in "2 to 10x fewer training steps" (Abstract, Section 1) potentially fragile. For instance, Table 1 lists specific peak steps (e.g., `@180`, `@100`), but without multiple seeds, it is unclear if these speedups are reproducible or artifacts of favorable initialization.

Ablation studies (Section 4.4, tables/ablation_q4_table.tex) show sensitivity to the entropy gate threshold ($\tau_{\mathrm{down}}$), yet these results also lack variance metrics. The "No-teacher" and "No-gate" failure modes (Figure 3, figures/fig_failure_modes.pdf) are qualitative; quantitative stability metrics (e.g., reward variance over time) would strengthen the evidence for the entropy gate's necessity. Additionally, while evaluation uses "avg@32" rollouts to reduce inference variance, this does not mitigate training variance. The effect sizes reported (e.g., +11.5 points on Qwen3-4B) are substantial, but without variance, statistical significance cannot be assessed. To meet NeurIPS standards for empirical evidence, the authors should report results averaged over at least 3-5 random seeds with standard deviations, or explicitly state the limitation of single-seed reporting in the text and discuss how it affects the robustness of the speedup claims. This aligns with the `paper_reviewer_statistical_analysis` prior review, reinforcing the need for more rigorous statistical evidence.
