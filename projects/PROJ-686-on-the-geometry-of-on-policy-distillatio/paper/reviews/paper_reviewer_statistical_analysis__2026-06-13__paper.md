---
action_items:
- id: 12e9b29593d1
  severity: science
  text: Add error bars or confidence intervals to trajectory plots (e.g., fig:intrinsic-metrics)
    to quantify variance across seeds.
- id: 49d0eb0751d2
  severity: science
  text: Report statistical significance (p-values or CIs) for performance comparisons
    in the rank-16 projection experiment.
- id: a41a42839c24
  severity: science
  text: Clarify whether main results are averaged over multiple seeds and justify
    the bf16 threshold eta=10^-3.
artifact_hash: 131dbc2ce86fd7fa8c00d7dd55a7501ac648ec7bf3f89711e549ef82e5ed9b1b
artifact_path: projects/PROJ-686-on-the-geometry-of-on-policy-distillatio/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-13T00:56:23.059373Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The paper presents compelling geometric diagnostics (stable rank, principal angles, spectral drift) to characterize On-Policy Distillation (OPD). However, the statistical analysis lacks necessary rigor regarding uncertainty and reproducibility. 

First, **uncertainty quantification is absent**. Figures such as `fig:intrinsic-metrics` and `fig:controls` depict single training trajectories without error bands. Stochastic optimization and sampling introduce variance; without reporting standard deviations or confidence intervals across multiple random seeds (mentioned in `tab:opd-variants` but not clearly reflected in main plots), it is impossible to assess the reliability of the observed trends. For instance, the claim that OPD stable rank is "narrow" requires showing that this stability persists across seeds.

Second, **hypothesis testing is missing**. Table `tab:update_sparsity` reports point estimates (e.g., OPD 51.6% vs SFT 8.1%). Without statistical tests (e.g., t-tests or ANOVA) or confidence intervals, we cannot confirm these differences are significant rather than random fluctuations. Similarly, the functional sufficiency claim in Section `sec:subspace-sufficient` compares OPD performance under rank-16 projection (64.2% vs 63.3%) without reporting variance or p-values. A 1% difference may not be statistically distinguishable from noise.

Third, **threshold justification is weak**. The bf16-aware sparsity metric uses a fixed threshold $\eta=10^{-3}$ (Appendix `app:diagnostic-implementation`). This choice impacts sparsity estimates significantly. A sensitivity analysis showing robustness to $\eta$ would strengthen the reproducibility of this diagnostic.

Finally, **seed reporting is inconsistent**. While `tab:opd-variants` lists "Multi-seed," the main text does not explicitly state whether results are averaged over seeds or represent a single run. For reproducibility, all main figures should reflect aggregated statistics from multiple independent runs.

Please address these statistical gaps by adding error bars, conducting significance tests for key comparisons, and clarifying the aggregation method for results.
