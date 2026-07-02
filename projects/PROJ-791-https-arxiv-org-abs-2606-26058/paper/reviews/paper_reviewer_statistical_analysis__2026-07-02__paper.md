---
action_items:
- id: ba39b79c1b1e
  severity: science
  text: Report variability metrics (standard deviation or confidence intervals) for
    all quantitative results in Table 1 and Table 2. Currently, only point estimates
    are provided, making it impossible to assess statistical significance or the robustness
    of the reported 18.7% improvement.
- id: 32837707f9ab
  severity: science
  text: Clarify the statistical methodology for the Human Preference Evaluation (Section
    4.2). With 40 volunteers ranking 20 videos, specify the aggregation method (e.g.,
    mean rank, Borda count) and the statistical test used to claim 'significant advantages'
    (e.g., Friedman test, Wilcoxon signed-rank).
- id: 42c70a2af5e7
  severity: science
  text: Define the sampling strategy for the 110 in-domain and 110 cross-domain test
    samples. Explicitly state if stratified sampling was used to ensure balanced representation
    of subjects/domains, and report the standard error of the mean for the reported
    metrics.
artifact_hash: 94f10ea6969d9a855608669bc738975c27d93327dc527ce8f35f4b9e47a4390d
artifact_path: projects/PROJ-791-https-arxiv-org-abs-2606-26058/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T13:45:44.966314Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis presented in the manuscript lacks the necessary rigor to support the strong claims of "significant" performance improvements. While the architecture and methodology are described in detail, the evaluation section relies almost exclusively on point estimates without measures of uncertainty.

**1. Lack of Variability Measures and Significance Testing**
In Table 1 (Quantitative results) and Table 2 (Ablation Studies), the authors report single scalar values for metrics such as CD-Score, NANO-CLIP, and GMEScore. There is no indication of whether these results are averages over multiple runs, seeds, or subsets of the test data. Without reporting standard deviations, standard errors, or confidence intervals (e.g., 95% CI), it is impossible to determine if the reported 18.7% improvement in CD-Score is statistically significant or merely a result of variance in the test set or random initialization. The claim of "significant improvement" in the text (Section 4.2) is unsupported by any statistical test (e.g., t-test, ANOVA) in the absence of variance data.

**2. Ambiguity in Human Preference Evaluation**
Section 4.2 describes a human preference study with 40 volunteers ranking 20 videos. The text states the method shows "significant advantages," but the statistical treatment of this ordinal data is missing. The review requires:
- The specific aggregation method used to convert rankings into scores.
- The statistical test employed to validate the significance of the differences (e.g., Friedman test for multiple comparisons, followed by post-hoc tests).
- The p-values associated with these tests.
Without this, the "significant" claim is anecdotal rather than statistical.

**3. Test Set Sampling and Robustness**
The test set construction (110 in-domain, 110 cross-domain) is described, but the sampling strategy is not detailed. Were these samples randomly drawn, or were they curated to be "hard" cases? If the latter, the generalizability of the results is limited. Furthermore, the standard error of the mean for the reported metrics should be calculated and reported to demonstrate the stability of the model's performance across the test distribution.

**Recommendation**
The authors must re-run the evaluation to include multiple seeds (if applicable) or bootstrap the test set to generate confidence intervals for all quantitative metrics. Additionally, a formal statistical test should be applied to the human preference data to substantiate the claim of significance. Until these statistical controls are in place, the magnitude of the claimed improvements cannot be scientifically verified.
