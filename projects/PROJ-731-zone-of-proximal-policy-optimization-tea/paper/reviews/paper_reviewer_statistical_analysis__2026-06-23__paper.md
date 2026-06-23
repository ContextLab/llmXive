---
action_items:
- id: 62c2fa987dbd
  severity: science
  text: "Provide statistical significance estimates (e.g., confidence intervals or\
    \ hypothesis\u2011test p\u2011values) for the primary macro\u2011average gains\
    \ reported in Table\u202F1 and Table\u202F2; the current presentation shows only\
    \ point percentages without uncertainty, making it unclear whether the observed\
    \ improvements are robust."
- id: 5fbcb08fac51
  severity: science
  text: "Address the multiple\u2011comparisons problem arising from evaluating many\
    \ benchmarks (31 total) and several baselines; consider applying a correction\
    \ (e.g., Bonferroni, Holm) or reporting family\u2011wise error rates."
- id: fbf561563466
  severity: science
  text: "Report results over multiple random seeds (at least three) for each method\
    \ to quantify run\u2011to\u2011run variance; include standard deviations or confidence\
    \ intervals for the main tables."
- id: 0b1ea0d0bd56
  severity: writing
  text: "Clarify the bootstrap procedure used in Appendix\u202FC (e.g., resampling\
    \ unit, number of replicates) and release the code used for the cluster\u2011\
    bootstrap analysis to ensure reproducibility."
- id: ea885da39730
  severity: writing
  text: Specify the random seed(s) and any nondeterministic settings (e.g., GPU nondeterminism,
    data shuffling) used during training and evaluation so that exact replication
    is possible.
artifact_hash: 0fd8fa2b8ede4e304df4503c08bd0823fb3038495b7a89b759c4ee4216df60db
artifact_path: projects/PROJ-731-zone-of-proximal-policy-optimization-tea/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-23T13:03:14.577879Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript introduces Zone of Proximal Policy Optimization (ZPPO) and reports impressive macro‑average improvements (e.g., +7.5 pp over the base model for the 0.8 B student). While the authors provide a cluster‑bootstrap analysis (Appendix C) with 95 % confidence intervals for ablation deltas, the main experimental tables (Table 1, Table 2, Table 3) lack any measure of statistical uncertainty. Point estimates alone do not convey whether the gains are statistically significant, especially given the large number of benchmarks (31) and multiple competing baselines (GRPO, Hint, Prefix, off‑/on‑policy distillation). 

The bootstrap analysis is a good step, but its scope is limited to pairwise comparisons in the ablation study; it is not applied to the primary results. Moreover, the manuscript does not discuss correction for multiple hypothesis testing across the many benchmark families, which could inflate Type I error rates. 

Another concern is the absence of repeated experiments with different random seeds. All reported numbers appear to be from a single run per configuration, yet RL training can be sensitive to initialization and stochasticity. Without reporting variance (e.g., standard deviation across seeds) or confidence intervals for the main results, the robustness of the claimed improvements cannot be assessed.

Reproducibility is further hampered by the lack of details on the bootstrap implementation (resampling unit, whether benchmarks are treated as independent, number of bootstrap replicates) and the omission of random seed specifications for both training and evaluation pipelines. Providing the exact code for the statistical analysis and the seeds used would greatly aid verification.

In summary, the statistical methodology is partially sound (bootstrap for ablations) but insufficient for the core claims. The paper would benefit from a more comprehensive statistical treatment of the primary results, explicit handling of multiple comparisons, and reporting of variability across random seeds. Addressing these points will strengthen the evidential basis of the work.
