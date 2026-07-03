---
action_items:
- id: f51b53b6c632
  severity: science
  text: In Section 7, the 95% CI calculation assumes 10,000 independent observations,
    ignoring the hierarchical structure (questions nested in videos/prompts). This
    likely underestimates variance. Please use cluster-robust SEs or mixed-effects
    models.
- id: f9a328ee82c5
  severity: science
  text: "Tables 1, 2, and 4 report only point estimates without uncertainty measures\
    \ (SD, SE, or CI). Given stochastic generation and LLM-as-judge variance, these\
    \ are insufficient to claim significance. Please report mean \xB1 SD over multiple\
    \ seeds."
- id: bfc825025fde
  severity: science
  text: Claims of 'state-of-the-art' in Table 4 (e.g., 48.9 vs 46.4) lack statistical
    significance testing (e.g., paired t-test, p-values). With high benchmark variance,
    these differences may not be significant. Please include p-values or effect sizes.
artifact_hash: 868016604b8d9a3bb37ad3c74cf4a71a551a99c22f54a694c5fb583a974a744e
artifact_path: projects/PROJ-665-https-arxiv-org-abs-2606-02800/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T12:40:15.871242Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in this manuscript is extensive in terms of the number of benchmarks reported, but it lacks rigor in quantifying uncertainty and establishing statistical significance.

The primary concern is the treatment of evaluation data as independent and identically distributed (i.i.d.) when the experimental design involves hierarchical dependencies. Specifically, in the **Cosmos-HUE** evaluation (Section 7, Appendix), the authors calculate a 95% confidence interval of ±0.6 points based on $N=10,000$ binary observations. However, the data generation involves 5 random-seed generations per prompt and up to 20 questions per video. This creates a nested structure where questions are not independent (sharing the same video) and videos are not independent (sharing the same prompt). Calculating the standard error as $\sqrt{p(1-p)/N}$ assumes independence across all observations, which is violated here. This likely leads to an underestimation of the true variance and overly narrow confidence intervals. The authors should re-calculate confidence intervals using cluster-robust standard errors (clustering by prompt or video) or a mixed-effects logistic regression model.

Furthermore, throughout the results sections (e.g., **Table 1**, **Table 2**, **Table 4**), the paper reports single point estimates for model performance (e.g., "91.36" on UniGenBench) without any accompanying measure of variability (standard deviation, standard error, or confidence intervals). In generative AI research, where results vary based on random seeds and the stochasticity of LLM-as-a-judge, reporting only point estimates is insufficient. It is impossible to determine if reported improvements over baselines are statistically significant. The authors should report results as mean ± standard deviation over multiple seeds or provide confidence intervals for all key metrics.

Finally, when claiming "state-of-the-art" in specific benchmarks (e.g., **Physics-IQ** in Table 4, where Cosmos3-Super scores 48.9 vs. Sora2's 46.4), the paper does not report statistical significance tests (e.g., paired t-tests). Given the high variance in these benchmarks, a difference of 2.5 points may not be significant. The authors should include p-values or effect sizes for critical comparisons to support their claims.
