---
action_items:
- id: a68c0eec1675
  severity: science
  text: Report confidence intervals or standard deviations for Pass@k and success
    rates in Tables 1 and 2. Single-point estimates from 116/117 tasks lack statistical
    context for significance claims.
- id: f9c384654f54
  severity: science
  text: Clarify the statistical test used to compare baselines (e.g., McNemar's test
    for paired binary outcomes). The paper claims 'strongest' performance without
    p-values or effect sizes.
- id: 277557799f2b
  severity: science
  text: Define the variance estimation method for the GRPO advantage estimator (Eq.
    12). Specify if group normalization uses population or sample variance, and how
    KL penalty variance is controlled.
artifact_hash: eb6909e8c26be542682832f5d7b13c92b92b728f8b94fb6c9612acad1621be79
artifact_path: projects/PROJ-782-mobileforge-annotation-free-adaptation-f/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T06:30:59.914375Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in the manuscript is largely descriptive, relying on point estimates (Pass@k, success rates) without measures of uncertainty or formal hypothesis testing. While the performance gains are numerically substantial (e.g., +25.0 pp in Table 3), the lack of confidence intervals (CIs) or standard deviations (SDs) makes it difficult to assess the reliability of these improvements, particularly given the relatively small test sets (116 tasks for AndroidWorld, 117 for MobileWorld).

In **Table 1 (AndroidWorld results)** and **Table 2 (MobileWorld results)**, the authors report single-point percentages (e.g., 77.6% vs 69.0%). For binary outcomes (success/failure) on a fixed set of tasks, the standard error can be approximated as $\sqrt{p(1-p)/n}$. For $n=116$ and $p \approx 0.7$, the 95% CI width is roughly $\pm 8.5\%$. The authors should explicitly report these intervals or the number of seeds used if results are averaged over multiple runs. Without this, claims of "strongest open-data performance" are statistically weak.

Furthermore, **Section 4.3 (Ablations)** presents comparisons (e.g., Hint vs. No Hint) but does not specify the statistical significance of the observed gains. A paired test (e.g., McNemar's test) is appropriate here since the same tasks are evaluated under different conditions. The absence of p-values or effect sizes leaves the reader unable to distinguish between genuine methodological improvements and random variance.

Regarding the **GRPO optimization (Section 3.3)**, the reward normalization (Eqs. 10-12) and KL regularization (Table 4) are described, but the statistical properties of the advantage estimator are not discussed. Specifically, the variance of the advantage estimates and the stability of the KL penalty across training steps (Figure 5) should be quantified. The training curves in **Figure 5** show reward trends but lack error bands (e.g., shaded regions for SD), which are standard for RL training analysis to demonstrate convergence stability.

Finally, the **task filtering ablation (Table 5)** compares SR ranges but does not account for the variance in sample sizes (1910 vs 2137 samples). A statistical justification for why the $[0.0, 0.9]$ range yields better generalization is needed beyond the observed point estimates.

To improve the statistical rigor, the authors should: (1) add CIs or SDs to all performance tables; (2) report p-values for key ablation comparisons; and (3) include error bands in training curves.
