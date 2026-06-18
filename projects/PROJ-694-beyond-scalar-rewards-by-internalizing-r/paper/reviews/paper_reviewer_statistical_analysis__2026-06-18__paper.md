---
action_items:
- id: b48978213bcd
  severity: science
  text: Report confidence intervals or standard errors for each evaluation metric
    (PLCC, SRCC, HPA, margin HPA) to quantify uncertainty and enable statistical significance
    testing.
- id: 56fd8c06dae8
  severity: science
  text: "Conduct appropriate statistical significance tests (e.g., paired bootstrap,\
    \ permutation tests) when comparing methods and clearly state p\u2011values or\
    \ effect sizes."
- id: 61ddb8ed315d
  severity: science
  text: "Apply a multiple\u2011comparison correction (e.g., Bonferroni, Holm\u2011\
    \u0160id\xE1k, or FDR) across the many pairwise method comparisons reported in\
    \ Table\u202F2 to control Type\u202FI error."
- id: c30f9b9442ff
  severity: writing
  text: "Provide details on random seeds, data splits, and any stochastic training\
    \ procedures (e.g., group size\u202FG, number of iterations) to ensure reproducibility\
    \ of the reported results."
- id: 3947f953d7ca
  severity: science
  text: "Include a brief discussion of the variance observed across multiple runs\
    \ (if any) and justify the choice of a single best\u2011performing run per model\
    \ size."
artifact_hash: ea1d74fbe2af288d803689e081136bb19c2463edb4534b816711d1532122572b
artifact_path: projects/PROJ-694-beyond-scalar-rewards-by-internalizing-r/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T00:49:59.108757Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript introduces a teacher‑student framework for visual reward modeling and evaluates several variants (Zero‑shot, SFT, RewardDance, GRPO, GDSO, RISD) on an internally annotated test set using PLCC, SRCC, human‑preference accuracy (HPA), and margin HPA. While the chosen metrics are appropriate for assessing calibration (PLCC, SRCC) and ranking quality (HPA), the statistical treatment of these results is insufficient.

1. **Absence of Uncertainty Quantification** (see Table 2, lines 162‑190). The authors report only point estimates for each metric. No confidence intervals, standard errors, or bootstrap distributions are provided, making it impossible to assess the reliability of the observed differences, especially given the modest sample sizes typical of human‑annotated preference datasets.

2. **No Significance Testing**. The paper claims that GDSO “substantially improves” over GRPO and that RISD “closely matches the larger teacher.” Without hypothesis tests (e.g., paired bootstrap or permutation tests) these statements lack statistical backing. This is particularly critical when differences are modest (e.g., PLCC 0.7620 vs. 0.7200 for the 27 B model).

3. **Multiple‑Comparison Issue**. The evaluation compares up to seven methods per model size across four metrics, leading to many pairwise comparisons. No correction for multiple hypothesis testing is applied, raising the risk of inflated Type I error rates. A correction method (Bonferroni, Holm‑Šidák, or FDR) should be reported.

4. **Reproducibility Details Missing**. The training pipeline (Algorithm 1) involves stochastic components (sampling G outputs, KL regularization, random initialization). The manuscript does not disclose random seeds, the number of training runs per configuration, or variance across runs. This hampers reproducibility and makes it unclear whether the reported numbers represent average performance or the best run.

5. **Effect Size Reporting**. Beyond p‑values, reporting effect sizes (e.g., Cohen’s d for HPA differences) would help readers gauge practical significance, especially when improvements are numerically small but statistically significant.

6. **Potential Over‑fitting to Validation Set**. The authors use the same held‑out test set for all model variants and also for hyper‑parameter tuning (e.g., λ values in Eq. (13)). Without a separate validation split or cross‑validation, there is a risk of over‑fitting the reported metrics.

**Recommendation:** The paper’s core idea is promising, but the statistical analysis must be strengthened before acceptance. The authors should augment Table 2 with confidence intervals, perform appropriate significance testing with multiple‑comparison correction, and provide full reproducibility details (random seeds, number of runs, variance). Addressing these points will substantiate the claimed performance gains and improve the scientific rigor of the work.
