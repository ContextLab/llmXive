---
action_items:
- id: 430b0a00076e
  severity: science
  text: "Provide measures of variability (e.g., standard deviation, confidence intervals)\
    \ for all reported performance numbers in Tables\u202F1\u20133 and the toy verification\
    \ (Table\u202F1). Without these, it is impossible to assess whether observed gains\
    \ are statistically significant."
- id: 26e3447b6ab4
  severity: science
  text: Report the number of random seeds or independent runs used for each experiment,
    and include the seed values or a statement that the same seed was used across
    baselines. This is essential for reproducibility of the statistical results.
- id: 72d8d99f5325
  severity: science
  text: "Conduct appropriate statistical significance tests (e.g., paired t\u2011\
    test or bootstrap) when comparing d\u2011OPSD against RLVR and SFT baselines across\
    \ the four reasoning tasks, and report p\u2011values. Adjust for multiple comparisons\
    \ (e.g., Bonferroni or Holm) given the six metrics (four tasks \xD7 two sequence\
    \ lengths)."
- id: 938d127ce4f6
  severity: science
  text: "Clarify the sampling strategy for the pass@k experiments (Section\u202F4.4.4).\
    \ Report the variance of the pass@k estimates (e.g., using the standard error\
    \ of a binomial proportion) to show the reliability of the reported improvements."
- id: 823914dbdb93
  severity: science
  text: "In the toy verification (Section\u202F4.1, Table\u202F1), include confidence\
    \ intervals for the Pass@1 and Pass@8 scores at each retaining ratio, and describe\
    \ the statistical test used to claim that the self\u2011teacher is \u2018significantly\
    \ better\u2019 than the student."
- id: 1369c5881bf0
  severity: writing
  text: Document any data preprocessing steps that could affect the distribution of
    the evaluation metrics (e.g., filtering of incorrect answers, thresholding for
    Sudoku scores). Provide justification that these steps do not bias the statistical
    comparison.
artifact_hash: 5c8da21032033f700374cf269bb9ef61b58d8799f1e6049fc84e38c052b8b257
artifact_path: projects/PROJ-732-learning-from-the-self-future-on-policy/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T12:42:26.582562Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents a novel on‑policy self‑distillation framework for diffusion LLMs (d‑OPSD) and reports impressive point estimates of reasoning performance (Tables 1–3). However, from a statistical‑analysis perspective the paper lacks essential quantitative rigor. All performance numbers are reported as single point values without any indication of variability (standard deviations, confidence intervals, or error bars). Consequently, readers cannot judge whether the observed improvements over RLVR and SFT baselines are statistically meaningful or could be due to random fluctuations.

The experimental sections (e.g., §4.2, Table 2) compare d‑OPSD against multiple baselines across four tasks and two generation lengths, amounting to at least eight paired comparisons. No correction for multiple hypothesis testing is discussed, raising the risk of inflated Type I error. Moreover, the paper does not specify how many random seeds or independent runs were performed; the training details (Appendix A) mention a single training run on four GPUs, but it is unclear whether the reported numbers are averages over runs or single runs. This omission hampers reproducibility and undermines confidence in the results.

The toy verification (Section 4.1, Table 1) samples 500 questions per task and reports Pass@1/Pass@8 scores for different retaining ratios. While the sample size is modest, the authors should still provide binomial confidence intervals (e.g., Wilson score intervals) to quantify uncertainty. The claim that “the self‑teacher significantly outperforms the student” is unsupported without a statistical test.

The sample‑efficiency comparison (Table 3) presents optimization step counts but does not assess whether the reduction from ~7 k steps to a few hundred steps is statistically robust across runs. Similarly, the ablation studies (e.g., retaining ratio, KL objective) lack error bars, making it impossible to discern whether observed differences are meaningful.

To strengthen the manuscript, the authors should (1) run each experiment with multiple random seeds (at least three) and report mean ± standard deviation; (2) compute 95 % confidence intervals for all metrics; (3) perform paired significance tests between d‑OPSD and each baseline, adjusting for the multiple comparisons inherent in the multi‑task evaluation; (4) describe any data filtering or thresholding that could bias the metrics; and (5) include these statistical details in the main text or supplementary material. Addressing these points will greatly improve the scientific rigor and reproducibility of the work.
