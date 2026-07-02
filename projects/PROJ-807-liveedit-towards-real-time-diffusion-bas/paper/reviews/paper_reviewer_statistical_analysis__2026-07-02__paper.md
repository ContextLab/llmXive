---
action_items:
- id: 1372f2003513
  severity: science
  text: The user study (Sec. X_suppl) reports percentages (e.g., 100.0%, 75.0%) from
    20 volunteers but lacks statistical significance testing (e.g., binomial test,
    chi-square) or confidence intervals to validate that the observed superiority
    over baselines is not due to chance.
- id: ac94d54a3d99
  severity: science
  text: Quantitative results in Tab. 1 and Tab. 2 report metrics to three decimal
    places without standard deviations or confidence intervals. Given the stochastic
    nature of diffusion models, variance estimates are required to assess the reliability
    of the reported SOTA claims.
- id: a6255f3acd84
  severity: science
  text: The claim of pruning '70% of redundant spatial tokens' (Sec. 4.1) is presented
    as a fixed empirical outcome. The manuscript should clarify if this threshold
    was optimized via cross-validation or if it represents a mean across the test
    set, and provide the variance of this pruning ratio.
artifact_hash: ad807d68c3634218d8a37b306582366b9db8e405a9dcf34fb28dd7323fcbdd9e
artifact_path: projects/PROJ-807-liveedit-towards-real-time-diffusion-bas/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T22:46:51.217265Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical rigor of the evaluation section requires strengthening to support the strong claims of state-of-the-art performance and real-time efficacy.

First, the **User Study** (Section "User Study" in `sec/X_suppl.tex`) relies on percentages derived from a sample size of $N=20$ volunteers. While the reported preference rates (e.g., 100.0% for Instruction Consistency) are striking, the absence of statistical significance testing (such as a binomial test against a null hypothesis of random choice or a chi-square test for independence) makes it difficult to rule out chance. Furthermore, no confidence intervals (e.g., 95% CI) are provided for these proportions, which is standard practice for human evaluation studies to indicate the precision of the estimate.

Second, the **Quantitative Comparisons** (Tables `tab/baseline.tex` and `tab/ablation_cache.tex`) present point estimates for metrics like Text Alignment and Background Consistency to three decimal places. Diffusion-based generation is inherently stochastic; therefore, reporting a single mean value without the standard deviation (std) or confidence intervals obscures the stability of the method. For instance, the difference between "Ours (W/ Cache)" (TA=0.270) and "Ours (W/o Cache)" (TA=0.265) appears marginal. Without variance data, it is impossible to determine if this improvement is statistically significant or within the noise floor of the evaluation metric.

Third, regarding the **AR-oriented Mask Cache** (Section 4.1, `sec/4_experiment.tex`), the authors state that the threshold $\tau$ is dynamically calculated to "explicitly prune 70% of the redundant spatial tokens." It is unclear if this 70% figure is a target hyperparameter, a mean achieved across the dataset, or a fixed constant. If it is a mean, the standard deviation of the pruning ratio across the 120 test pairs should be reported to demonstrate the consistency of the cache's behavior. If it is a fixed target, the text should clarify that the threshold $\tau$ is adjusted per frame to meet this specific sparsity constraint, rather than being a static value.

Finally, the **Ablation Study** (Table `tab/ablation-arch.tex`) compares latency and quality across stages. While the latency drop is dramatic, the quality metrics (Text Alignment, Image Quality) show minor fluctuations (e.g., 0.268 vs 0.264). Without statistical testing or error bars, the claim that Stage 3 "maintains high-quality editing performance" despite the aggressive distillation is not fully statistically substantiated. The authors should add variance metrics to all quantitative tables and perform significance tests on the user study results.
