---
action_items:
- id: f646996aff40
  severity: science
  text: Report statistical variability (e.g., standard deviations or confidence intervals)
    for all quantitative metrics (FID, IS, sFID, precision, recall) across multiple
    random seeds or repeated runs.
- id: 0cfd9e29190f
  severity: science
  text: Provide details on random seed initialization and any stochastic components
    of training/evaluation to enable exact reproducibility.
- id: aac8f60f2353
  severity: science
  text: "When performing multiple ablations (e.g., static vs. dynamic query, chunk\
    \ sizes, timestep\u2011injection variants), apply appropriate multiple\u2011comparison\
    \ corrections or clearly state that each comparison is independent."
- id: 05eb77903984
  severity: writing
  text: "Include a brief statistical justification for the number of samples (50\u202F\
    k) used for evaluation and discuss whether this sample size yields stable estimates\
    \ of the reported metrics."
artifact_hash: 7a4bc7e64a39662319f7490ada4c2be57d6c20dd18ca5f1225c2e0b697bf14b3
artifact_path: projects/PROJ-625-https-arxiv-org-abs-2605-20708/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-24T18:00:58.128750Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents extensive empirical results for the proposed Diffusion‑Adaptive Routing (DAR) mechanism, but the statistical treatment of these results is insufficient. All performance numbers (FID, IS, sFID, precision, recall) are reported as single point estimates without any indication of variability or statistical significance. There is no mention of how many random seeds were used, whether the reported numbers are averages over multiple runs, or whether confidence intervals were computed. Given the known variance of generative model evaluation metrics, especially FID, the lack of such information makes it difficult to assess whether the observed improvements (e.g., a 2.11 FID reduction) are robust or could be due to random fluctuations.

The diagnostic analyses (forward magnitude, gradient magnitude, block‑wise similarity) also lack statistical rigor: the paper presents curves but does not quantify the uncertainty of these measurements, nor does it test whether the differences between baseline and DAR are statistically significant across the sampled ImageNet subset. Moreover, multiple ablation studies (static vs. dynamic queries, timestep‑injection, chunk size, REPA compatibility) are performed, yet the manuscript does not address the multiple‑comparison problem; without correction, the risk of false positives increases.

Reproducibility is further hampered by the absence of random seed specifications, details on stochastic training components (e.g., data shuffling, dropout), and the exact version of the codebase used. While the authors provide extensive implementation details in the appendix, the lack of explicit seed information and version control metadata prevents exact replication of the reported results.

To strengthen the statistical validity of the work, the authors should:

1. Run each experimental configuration across several random seeds (at least 3–5) and report mean ± standard deviation or 95 % confidence intervals for all metrics.
2. Clearly state the random seed(s) used for the primary results and provide a script or configuration file that sets these seeds.
3. Discuss the choice of 50 k samples for evaluation, possibly providing an analysis of metric stability as a function of sample size.
4. When comparing many variants, either apply a multiple‑comparison correction (e.g., Bonferroni or Holm) or explicitly treat each comparison as a separate hypothesis with appropriate justification.

Addressing these points will make the empirical claims more credible and the work more reproducible.
