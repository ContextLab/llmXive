---
action_items:
- id: d29d9ee45943
  severity: science
  text: "Report variance (e.g., standard deviation or confidence intervals) for all\
    \ aggregate metrics (pre\u2011training loss reductions, downstream accuracy averages,\
    \ perplexity) and perform statistical significance testing (e.g., paired t\u2011\
    tests or bootstrap) to substantiate the claimed improvements."
- id: a4e4881f974c
  severity: science
  text: Specify the number of random seeds / training runs used for each experimental
    configuration and provide the seed values or a reproducibility statement.
- id: 342e7fc7ff8f
  severity: science
  text: "Address multiple\u2011comparison issues when evaluating across 25 downstream\
    \ benchmarks; consider correcting p\u2011values (e.g., Bonferroni or Holm) or\
    \ reporting per\u2011task significance."
- id: 6f69fa3ef8d0
  severity: science
  text: "Include details on how the load\u2011balancing metrics (MaxVio) were computed\
    \ (e.g., batch size, number of evaluation steps) and report their variability."
- id: 3aa51b1845c5
  severity: science
  text: "Provide the exact hyperparameter values for the constant C (including C\u2032\
    ) used in the large\u2011scale experiments and any sensitivity analysis results,\
    \ to enable independent replication."
artifact_hash: 34fabb025335fc2fcf0855d53316dbb275a62eee03c0f1ad1b72c49ea11b1392
artifact_path: projects/PROJ-697-redesign-mixture-of-experts-routers-with/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T04:39:21.335017Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript introduces a principled router redesign for Mixture‑of‑Experts (MoE) models, aligning each router row with the principal singular direction of its associated expert via a single‑step power iteration followed by L₂‑norm retraction. While the methodological contribution is clearly articulated, the statistical analysis supporting the empirical claims is insufficient.

**Statistical Reporting Deficiencies**
- The paper reports average improvements (e.g., +1.44 % downstream accuracy, loss reductions) without any measures of dispersion (standard deviation, confidence intervals) or significance testing. Given the variability inherent in large‑scale language model training, these point estimates alone do not establish that the observed gains are robust.
- No information is provided on the number of random seeds or independent training runs per configuration. Without replication details, it is impossible to assess the reproducibility of the results.
- The evaluation spans 25 downstream benchmarks, yet the authors treat the average as a single metric without addressing the multiple‑comparison problem. Reporting per‑task significance or applying a correction (e.g., Bonferroni, Holm) is necessary to avoid inflated Type I error rates.
- Load‑balancing metrics (MaxVio) are presented as single numbers; their statistical variability across training steps or runs is not reported.

**Reproducibility Concerns**
- Hyperparameters for the scaling constant C (and its derived C′) are discussed qualitatively, but exact values used in the 3 B and 11 B experiments are absent. The sensitivity analysis in Table 9 uses a small‑scale setting, but the transfer to large‑scale models is not quantified.
- The code snippets (Figure 2) lack details on random seed initialization and deterministic settings (e.g., cuDNN flags), which are essential for exact replication.

**Recommendations**
To strengthen the empirical claims, the authors should:
1. Run each experimental configuration with multiple random seeds (at least three) and report mean ± standard deviation (or 95 % confidence intervals) for all key metrics.
2. Perform appropriate statistical tests (paired tests for ablations, bootstrap for downstream accuracies) and report p‑values, correcting for the multiple benchmarks evaluated.
3. Document the exact values of C (and C′) used in each scale, and include the results of the sensitivity analysis for those scales.
4. Provide a reproducibility checklist covering seed settings, hardware configuration, and any nondeterministic operations.

Addressing these points will allow the community to assess the significance and reliability of the reported improvements and will make the work fully reproducible.
