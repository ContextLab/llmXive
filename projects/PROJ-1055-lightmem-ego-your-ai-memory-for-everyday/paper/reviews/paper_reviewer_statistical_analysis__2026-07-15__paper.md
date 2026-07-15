---
action_items:
- id: 65cc37eae3d3
  severity: writing
  text: Tables 1 and 2 report QA and retrieval metrics (e.g., 51.9% LLM-judge accuracy)
    as single point estimates without any measure of uncertainty (SD, SE, or CI).
    Given the small sample size implied by the integer percentages (likely N=9 per
    scenario), the variance is likely high. Report the standard deviation or 95% confidence
    intervals for all reported metrics, or explicitly state the exact N and that these
    are single-run results.
- id: 2e19ef7d4c0d
  severity: writing
  text: Section 5.1 and 5.2 claim LightMem-Ego is 'better' or 'more accurate' than
    baselines in the text, but Table 4 (capability comparison) only lists binary features
    (checkmarks) without quantitative performance data. No statistical test (e.g.,
    paired t-test, Wilcoxon) or confidence interval is provided to support any claim
    of superiority over the listed systems. Either remove comparative claims of 'better'
    performance or provide the underlying quantitative data and appropriate statistical
    tests.
artifact_hash: edb07ae94c2d6219a9932968c85762643ccbb6eec8694c7f370d843f8e0e853b
artifact_path: projects/PROJ-1055-lightmem-ego-your-ai-memory-for-everyday/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-15T03:57:01.482154Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical reporting in Section 5 (Quantitative Evaluation) and the associated tables (tables/recall.tex, tables/accuracy.tex) lacks necessary measures of uncertainty and rigorous comparative testing.

First, the reported metrics in Table 1 (Recall) and Table 2 (QA Accuracy) are presented as precise point estimates (e.g., "51.9%", "74.1%") without any accompanying standard deviation (SD), standard error (SE), or confidence intervals (CI). The integer nature of the per-scenario scores (e.g., 44.4, 33.3, 77.8) strongly suggests a very small sample size (likely N=9 queries per scenario). With such small N, the sampling variance is substantial, and a single point estimate is misleadingly precise. The authors must report the variability across the test set (e.g., "51.9% ± 12.3%") or provide 95% confidence intervals to allow readers to assess the stability of these results.

Second, the text in Section 5.1 and 5.2 makes qualitative claims of superiority (e.g., "LightMem-Ego retrieves relevant memory evidence... for most queries," "best performance on life summarization") but does not statistically validate these claims against the baselines or across scenarios. Table 4 (Capability Comparison) is a qualitative feature matrix, not a quantitative performance benchmark. There are no p-values, effect sizes, or statistical tests (such as paired t-tests or non-parametric equivalents) reported to support any assertion that LightMem-Ego is "significantly" or "statistically" better than the listed systems (e.g., Vinci, Mem0). While the paper frames this as a demonstration, any claim of comparative performance requires statistical backing or a clear disclaimer that the comparison is qualitative only.

Finally, the latency results in Table 3 (Latency) report P50 and P90 values but omit the sample size (N) or the distribution shape (e.g., standard deviation). While percentiles are robust, reporting the N is essential to judge the reliability of the P90 estimate, especially given the high variance typical in network-dependent systems.

These are reporting issues that can be fixed by adding the missing statistics to the tables or clarifying the text to reflect the lack of statistical significance testing, without requiring new experiments.
