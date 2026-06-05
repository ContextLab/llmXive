---
action_items:
- id: 0d22fc7db070
  severity: science
  text: Report confidence intervals or standard errors for all benchmark scores (e.g.,
    MMLongBench, MM-NIAH) to quantify evaluation uncertainty, particularly given LLM-based
    judging mentioned in Appendix.
- id: 36d21d720665
  severity: science
  text: Address multiple-comparisons inflation in ablation studies (Section 5, Appendix)
    by correcting p-values or explicitly acknowledging hyperparameter search bias
    when claiming optimal ratios.
artifact_hash: 64fda0b4c326e1fc50df1dd3551145b206b04e1dae0b0745067541ff9112fca2
artifact_path: projects/PROJ-575-training-long-context-vision-language-mo/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-05T10:58:14.936908Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents a compelling empirical study of long-context continued pre-training (LongPT). However, the statistical rigor supporting the quantitative claims requires strengthening before publication. 

First, all performance comparisons rely on point estimates without measures of uncertainty. Table 1 (Section 4) reports a 7.1% improvement in average long-document VQA scores (50.59 vs 57.70), but provides no confidence intervals or standard errors. Given the use of LLM-based judging for binary and F1 scores (Appendix, Section A.2), evaluation variance is non-trivial. Without bootstrap confidence intervals or repeated runs (e.g., 3 seeds), it is impossible to determine if the reported gains are statistically significant or artifacts of random variation in the evaluation pipeline.

Second, the ablation studies in Section 5 and the Appendix suffer from multiple-comparisons issues. The authors grid-search extraction-to-reasoning ratios (Table 2) and mRoPE base frequencies (Appendix Table 3) to identify optimal configurations. No correction for multiple hypothesis testing (e.g., Bonferroni or FDR) is applied when selecting the "best" settings. This increases the risk of overfitting to the specific validation set and inflating the significance of the chosen hyperparameters. The claim that the 8:2 ratio is superior lacks statistical backing against the other tested ratios.

Finally, reproducibility is hindered by the lack of training seeds. The data synthesis pipeline involves sampling 8-15 page segments and using a teacher model (Seed 2.0), both introducing stochasticity. Reporting results from a single training run prevents verification of stability. 

To resolve these concerns, the authors should either provide error bars based on multiple evaluation seeds or explicitly state the limitation of single-run reporting. Additionally, a discussion on the statistical power of the benchmark sample sizes is necessary to contextualize the observed effect sizes. These changes are critical to ensure the reported improvements are robust and not statistical flukes.
