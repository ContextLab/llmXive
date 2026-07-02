---
action_items:
- id: ae6cbf1795cb
  severity: science
  text: "The manuscript presents a novel Parallel Box Decoding (PBD) approach but\
    \ lacks rigorous statistical validation for its core empirical claims. First,\
    \ the data quality assertions in the Abstract are statistically unsupported. The\
    \ claim of a \"14.2% rejection rate\" across 138M samples and \"99.4% agreement\"\
    \ on a 500-sample spot-check lacks necessary statistical context. The authors\
    \ must report the confidence interval for the 99.4% agreement rate (which, for\
    \ n=500, is approximately \xB11.3% at 95% confid"
artifact_hash: c8578cab24ae10f85328a488241d9cfe1b5d4266743783cf5e0239d549de8c29
artifact_path: projects/PROJ-636-locateanything-fast-and-high-quality-vis/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T12:26:57.364128Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: full_revision
---

The manuscript presents a novel Parallel Box Decoding (PBD) approach but lacks rigorous statistical validation for its core empirical claims. 

First, the data quality assertions in the Abstract are statistically unsupported. The claim of a "14.2% rejection rate" across 138M samples and "99.4% agreement" on a 500-sample spot-check lacks necessary statistical context. The authors must report the confidence interval for the 99.4% agreement rate (which, for n=500, is approximately ±1.3% at 95% confidence) and explicitly define the sampling strategy used for the spot-check. Without this, the generalizability of the quality control to the full 138M dataset is unproven.

Second, the throughput and performance comparisons rely solely on point estimates. For instance, the claim of "12.7 BPS" versus "1.1 BPS" (Section 5.2) is presented without standard deviations, confidence intervals, or results from statistical significance tests (e.g., paired t-tests). In systems benchmarking, variance due to hardware thermal throttling or batch size fluctuations is common; a single measurement is insufficient to substantiate a "10x faster" claim.

Third, the ablation studies (Table 3) involve multiple pairwise comparisons of F1 scores across different modes and representations. The manuscript fails to address the multiple-comparisons problem. Without corrections (e.g., Bonferroni), the probability of observing at least one statistically significant difference by chance increases with the number of tests performed. The authors should either apply such corrections or provide p-values for the reported improvements.

Finally, all performance metrics in Tables 2, 4, and 5 are reported as single values. Standard practice in computer vision requires reporting standard errors or 95% confidence intervals to distinguish genuine model improvements from evaluation noise. The absence of these metrics makes it impossible to assess the statistical robustness of the reported "SOTA" results.
