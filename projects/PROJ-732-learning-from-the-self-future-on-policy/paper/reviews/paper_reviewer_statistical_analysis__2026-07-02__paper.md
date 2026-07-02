---
action_items:
- id: f718b23f6482
  severity: science
  text: Report confidence intervals or standard deviations for all reported accuracy
    metrics in Tables 1-8. Single-point estimates without variance measures (e.g.,
    from multiple seeds) make it impossible to assess statistical significance of
    the claimed improvements over baselines.
- id: 641f7c0e711a
  severity: science
  text: Clarify the statistical test used to claim 'consistent outperformance' in
    Section 4.2. With only 4 tasks and varying sequence lengths, a formal test (e.g.,
    paired t-test or Wilcoxon signed-rank) across seeds is required to support the
    claim that d-OPSD is statistically superior to diffu-GRPO.
- id: f2db04d29f30
  severity: science
  text: The ablation studies in Section 4.4 (Tables 5-8) present single-point results.
    Provide variance estimates (e.g., standard error) for these ablation results to
    determine if observed differences (e.g., 81.0 vs 80.5) are statistically significant
    or within noise.
artifact_hash: 5c8da21032033f700374cf269bb9ef61b58d8799f1e6049fc84e38c052b8b257
artifact_path: projects/PROJ-732-learning-from-the-self-future-on-policy/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T04:41:55.936249Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents a novel framework, d-OPSD, for on-policy self-distillation in diffusion large language models. While the methodological adaptation is sound, the statistical rigor of the experimental evaluation is insufficient for a top-tier venue.

**Lack of Variance Reporting:**
The primary statistical deficiency is the absence of variance estimates for all quantitative results. Tables 1 through 8 report single-point accuracy scores (e.g., "81.0" for GSM8K in Table 2) without standard deviations, standard errors, or confidence intervals. In deep learning experiments, performance can vary significantly across random seeds due to initialization and stochastic optimization. Without reporting results averaged over multiple seeds (e.g., $N \ge 3$) with error bars, it is impossible to determine if the reported improvements (e.g., the 1.2% gain over diffu-GRPO in Table 2) are statistically significant or merely artifacts of a specific random seed. The claim of "consistent outperformance" in Section 4.2 is not statistically supported by single-point estimates.

**Missing Significance Testing:**
The paper claims d-OPSD "consistently outperforms" baselines (Section 4.2) and that specific ablation choices (e.g., $\rho_\text{teacher}=0.25$ vs $0.10$ in Table 6) yield better results. However, no statistical hypothesis tests (e.g., paired t-tests or Wilcoxon signed-rank tests) are performed to validate these claims. Given the small number of tasks (4) and the likely high variance in LLM reasoning benchmarks, formal testing is required to distinguish signal from noise.

**Ablation Study Rigor:**
The ablation studies in Section 4.4 (Tables 5-8) are critical for validating the design choices (e.g., step-level vs. token-level, retaining ratios). Currently, these tables present single runs. The differences observed (e.g., 81.0 vs 79.8 in Table 6) are small and may not be robust. The authors must re-run these ablations with multiple seeds and report the mean $\pm$ standard deviation to confirm that the chosen hyperparameters are genuinely optimal and not overfit to a specific run.

**Sample Efficiency Claims:**
The claim of "superior sample efficiency" (Section 4.2, Table 3) relies on comparing convergence steps. While the step counts are distinct (425 vs 7700), the learning curves (Figure 1) lack error bands. To robustly support the efficiency claim, the learning curves should show performance variance over time, demonstrating that the faster convergence is consistent and not a fluke of the specific training trajectory.

In summary, the paper requires a statistical overhaul of its experimental section. The authors should re-run experiments with multiple seeds, report mean $\pm$ standard deviation for all metrics, and apply appropriate statistical tests to validate their comparative claims.
