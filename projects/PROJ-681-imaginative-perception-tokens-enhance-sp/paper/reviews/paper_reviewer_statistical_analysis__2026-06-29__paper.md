---
action_items:
- id: 3cea8a06c156
  severity: science
  text: Report confidence intervals or standard deviations for all accuracy metrics.
    Tables tab:pt_breakdown, tab:qwen_discrete, and tab:qwen_modality show point estimates
    only without variance measures across random seeds or runs.
- id: 87a966323556
  severity: science
  text: Perform statistical significance testing when comparing model variants. Claims
    of improvement (e.g., 55.0% to 59.6% PT accuracy in tab:qwen_modality) lack p-values
    or bootstrap tests to establish significance.
- id: da5f77ccfa62
  severity: science
  text: Report test set sizes for all benchmarks to assess statistical power. Section
    supp_data mentions training set sizes but omits test set counts needed to evaluate
    metric reliability.
- id: 4f2a4d9ebc4c
  severity: science
  text: Address multiple-comparisons correction when evaluating across three tasks
    (Path Tracing, Perspective Taking, Multiview Counting) and multiple model variants
    without adjustment.
artifact_hash: c5de9734fccbfd100241f7fc8603c599264726354d7ecbedd4d657c0e121782f
artifact_path: projects/PROJ-681-imaginative-perception-tokens-enhance-sp/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T10:17:35.307376Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: full_revision
---

This review focuses exclusively on statistical analysis rigor. The paper presents accuracy metrics across multiple benchmarks and model variants but lacks essential statistical reporting required to validate claims of improvement.

**Critical Statistical Gaps:**

1. **No Variance Reporting**: Tables `tab:pt_breakdown`, `tab:qwen_discrete`, and `tab:qwen_modality` report single-point accuracy estimates without standard deviations, confidence intervals, or results across multiple random seeds. In Section `supp_vlms`, the claim that grayscale IPT improves PT from 55.0% to 59.6% cannot be assessed for statistical significance without variance measures.

2. **Missing Significance Tests**: When comparing Bagel (base) vs. Bagel (label-only) in `tab:pt_breakdown` (e.g., 36.3% vs. 73.5% on EgoDir), no statistical tests (paired t-tests, bootstrap tests, or McNemar's test) are reported. Without these, observed differences could reflect random variation rather than genuine model improvements.

3. **Test Set Sizes Unreported**: Section `supp_data` details training set sizes (e.g., 55,529 Perspective Taking samples) but omits test set counts. Without knowing test set sizes, readers cannot assess statistical power or the reliability of reported accuracy percentages.

4. **Multiple Comparisons**: The paper evaluates three tasks (Path Tracing, Perspective Taking, Multiview Counting) with multiple model variants and input settings. No correction for multiple comparisons (e.g., Bonferroni, Holm-Bonferroni) is mentioned, increasing false-positive risk when claiming improvements.

5. **Reproducibility Concerns**: No information is provided about the number of training runs, random seeds used, or whether results represent averages across runs. This limits reproducibility and makes it impossible to assess result stability.

**Required Actions:**

- Report accuracy with ±standard deviation or 95% confidence intervals across at least 3 random seeds for all main results tables.
- Include statistical significance tests (with p-values) when comparing model variants.
- Report test set sizes for all benchmarks.
- Discuss multiple-comparisons handling when making claims across multiple tasks/benchmarks.
- Document the number of random seeds and training runs in the experimental setup section.

Without these statistical safeguards, the paper's central claim that IPT enhances spatial reasoning lacks rigorous empirical support.
