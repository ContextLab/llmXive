---
action_items:
- id: d1a7410ec32c
  severity: writing
  text: Clarify the degrees of freedom (df) reported in Table 1 and Supplementary
    Tables. The df values are non-integers (e.g., 31.53, 16.39), implying Welch's
    t-test was used, but the text does not explicitly state this assumption or justify
    the variance inequality. Explicitly name the test variant used.
- id: 5a2261f2219a
  severity: science
  text: Address the multiple comparisons problem. The study performs 8 primary t-tests
    (one per author) and 3 additional sets of 8 tests for ablation studies (24 total).
    The text reports uncorrected p-values (e.g., p < 0.001). Apply a correction method
    (e.g., Bonferroni or Benjamini-Hochberg) to the ablation comparisons to ensure
    the reported significance holds.
- id: 2f29d3bb6cd8
  severity: science
  text: Justify the use of 10 random seeds as the basis for statistical inference.
    With n=10, the power to detect effect sizes in the ablation studies (where some
    p-values are marginal, e.g., p=0.0529 for Melville in function-word models) is
    low. Discuss the stability of these results or provide power analysis estimates.
artifact_hash: 148021f63314c6cbe2b6159eaaaecc4e6c793ec5541ddbe74681664a10cdde19
artifact_path: projects/PROJ-562-a-stylometric-application-of-large-langu/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:16:34.389783Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis presented in the manuscript is generally robust in its experimental design, particularly the use of 10 random seeds to generate distributions for hypothesis testing. The core finding—that models trained on a specific author yield significantly lower cross-entropy loss on that author's held-out text compared to others—is supported by strong effect sizes and highly significant p-values in the primary analysis (Table 1).

However, several statistical reporting and inference details require clarification and correction before the results can be fully accepted.

First, the degrees of freedom (df) reported in Table 1 and the Supplementary Tables are non-integers (e.g., df = 31.53 for Baum, df = 16.39 for Thompson). This indicates the authors utilized Welch’s t-test (which does not assume equal variances) rather than the standard Student’s t-test. While this is often the more appropriate choice, the manuscript text (Section "Results") does not explicitly state that Welch’s t-test was used. The methods section should be updated to specify the exact statistical test variant employed to ensure reproducibility and clarity regarding the assumption of variance homogeneity.

Second, the manuscript does not address the issue of multiple comparisons. The authors conduct a series of hypothesis tests: 8 primary tests for the main authors, and then 3 additional sets of 8 tests for the ablation studies (content-only, function-only, POS-only), totaling 32 tests. The reported p-values are uncorrected. For the ablation studies, where some results are marginal (e.g., Melville in the function-word model, p = 0.0529 in Supp. Tab. 2), the lack of correction (such as Bonferroni or Benjamini-Hochberg) is a significant concern. The authors should apply a correction method to the ablation comparisons and report the adjusted p-values to confirm that the conclusions regarding the relative effectiveness of content vs. function words remain valid.

Finally, the statistical power of the analysis relies on n=10 (the number of random seeds). While sufficient for the main effect (which shows massive separation), the power is limited for the ablation studies where effect sizes are smaller. The discussion of the POS-only results (where the average t-value was not reliably greater than zero, p=0.141) would benefit from a brief comment on the stability of these null results given the small sample size. The authors should ensure that the claim that "POS sequences... appear to be more similar across authors" is not an artifact of low power, although the trend is consistent across the data.

Overall, the statistical approach is sound, but the reporting of test assumptions and the handling of multiple comparisons need to be tightened to meet rigorous standards.
