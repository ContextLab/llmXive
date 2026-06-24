---
action_items:
- id: 9e8d57503fbe
  severity: science
  text: Provide measures of variability (e.g., standard deviation, confidence intervals)
    for all reported metrics (ADE, FDE, PWT, robot success rates, video quality scores)
    and perform appropriate statistical significance tests when comparing models.
- id: 1f4dd308d6a5
  severity: science
  text: "Describe the random seed handling, data split procedures, and any hyper\u2011\
    parameter search strategy to ensure reproducibility of the experiments."
- id: 87349a679341
  severity: science
  text: "Address the multiple\u2011comparisons problem arising from evaluating many\
    \ baselines across three datasets; apply corrections (e.g., Bonferroni, Holm)\
    \ or clearly justify why they are unnecessary."
- id: 86bf740a5215
  severity: writing
  text: "Clarify the best\u2011of\u20115 evaluation protocol: specify whether metrics\
    \ are averaged over the five runs per sample and report the distribution of those\
    \ runs."
- id: 5124f84e55d2
  severity: science
  text: Release the code and exact training/evaluation scripts (including versioned
    dependencies) to allow independent verification of the statistical results.
artifact_hash: 43d44b1b7f12aef158eaf0787875484ea72c6860cf8af3c796e4579ec99e55ab
artifact_path: projects/PROJ-741-molmomotion-forecasting-point-trajectori/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-24T15:40:27.578349Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents a novel task—goal‑conditioned 3D point motion forecasting—and introduces a large‑scale dataset, a model, and several downstream applications. While the engineering contributions are compelling, the statistical analysis of the experimental results is insufficient for a rigorous scientific claim.

**Metric Reporting and Variability**  
Tables 1, 2, 3, 4, 5, 6, and 7 report point estimates (e.g., ADE, FDE, PWT, robot success rates, VBench scores) without any indication of variability (standard deviations, confidence intervals, or inter‑quartile ranges). The “best‑of‑5” evaluation is mentioned, but it is unclear whether the reported numbers are averages over the five runs per sample, the best single run, or something else. Without variability estimates, readers cannot assess whether observed differences (e.g., the 0.109 m ADE of MolmoMotion‑AR vs. 0.135 m of the flow‑matching variant) are statistically meaningful.

**Statistical Significance Testing**  
The paper compares many baselines across three benchmark subsets (HOT3D, WorldTrack, DAVIS). No hypothesis tests (e.g., paired t‑tests, Wilcoxon signed‑rank) are performed, nor are p‑values or effect sizes reported. Consequently, claims such as “MolmoMotion outperforms prior methods by a large margin” lack quantitative support.

**Multiple Comparisons**  
Given the large number of models and metrics, the risk of false positives is high. The manuscript does not discuss any correction for multiple hypothesis testing (e.g., Bonferroni, Holm‑Šidák) or provide a rationale for why such corrections are unnecessary. This omission further weakens the evidential basis for the reported superiority of the proposed method.

**Reproducibility Details**  
Key reproducibility information is missing: random seed values, exact train/validation split definitions for the benchmark, and details of any hyper‑parameter tuning (grid search ranges, selection criteria). Although the appendix lists many implementation details, the lack of explicit seed handling and split specifications makes it difficult for an independent researcher to replicate the results.

**Downstream Robotics Evaluation**  
Success rates in Fig. 5a are presented as single percentages without confidence intervals or statistical tests. Given the stochastic nature of reinforcement‑learning‑style finetuning, reporting variability (e.g., binomial confidence intervals) is essential to substantiate claims of “substantially improves training efficiency and final performance.”

**Video Generation Metrics**  
The VBench scores in Table 5 are point estimates without variance. Since these metrics are computed over a relatively small set of generated videos, reporting standard errors would help gauge the reliability of the observed differences.

**Overall Assessment**  
The experimental pipeline is well‑described, but the statistical treatment of the results is under‑developed. Adding variability estimates, significance testing, multiple‑comparison corrections, and full reproducibility documentation would substantially strengthen the paper’s scientific rigor.
