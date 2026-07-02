---
action_items:
- id: 5ed2e25d4446
  severity: writing
  text: The statistical rigor of the evaluation framework requires clarification to
    support the paper's central claims regarding the "Clever Hans" effect and the
    efficacy of the proposed alignment recipe. First, the primary results in Table
    1 (e001, line 134) and Table 2 (e001, line 168) present point estimates of accuracy
    (e.g., 83.1%, 1.4%) without any measure of variance (standard deviation, confidence
    intervals, or standard error). Given that these metrics are derived from finite
    test sets, the abse
artifact_hash: e83058c54d1a49095166f0ef2ff7177a4db8d52f3626563ad7ae59fa949315e9
artifact_path: projects/PROJ-610-https-arxiv-org-abs-2605-16403/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T19:17:03.195612Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical rigor of the evaluation framework requires clarification to support the paper's central claims regarding the "Clever Hans" effect and the efficacy of the proposed alignment recipe.

First, the primary results in **Table 1** (e001, line 134) and **Table 2** (e001, line 168) present point estimates of accuracy (e.g., 83.1%, 1.4%) without any measure of variance (standard deviation, confidence intervals, or standard error). Given that these metrics are derived from finite test sets, the absence of uncertainty bounds makes it impossible to determine if the observed differences between models (e.g., MiniCPM-o-4.5 vs. MiMo-V2.5) or the improvement from the baseline (34.3% to 83.1%) are statistically significant or potentially due to random sampling noise. The authors should report 95% confidence intervals for all accuracy metrics, calculated via bootstrapping or binomial proportion methods, to substantiate the magnitude of the reported gains.

Second, the calculation of the **"Avg Gap"** metric in Table 1 lacks statistical context. While the appendix defines the formula as an average of accuracy drops, the text does not address the issue of multiple comparisons. The study evaluates six models across three distinct intervention types (Shift, Mute, Swap). Without a correction for multiple testing (e.g., Bonferroni or False Discovery Rate) or a clear statement on the independence of these tests, the risk of Type I errors in claiming "systematic shortcut reliance" across all models is elevated. The authors should clarify if the reported gaps are statistically distinguishable from zero after correction.

Third, the sample size and distribution for the training data are insufficiently detailed. The abstract and Section 3 mention a "10K-sample recipe" (e000, line 10; e001, line 10), but the breakdown of these samples across the three intervention categories (Shift, Mute, Swap) is not provided. If the 28% average gain is driven by a specific intervention with a disproportionately large sample size, the generalizability of the claim is compromised. A power analysis or a clear statement of the sample size per condition is necessary to validate the robustness of the alignment results.

Finally, the definition of the "Mute Hallucination" rate (e002, line 10) relies on a binary classification by an LLM judge. The statistical properties of this judge (e.g., inter-rater reliability, false positive rate) are not reported. If the judge has a non-negligible error rate, the reported hallucination rates (e.g., >0.63) may be biased. The authors should provide validation metrics for the automated evaluation protocol to ensure the statistical validity of the failure-mode analysis.
