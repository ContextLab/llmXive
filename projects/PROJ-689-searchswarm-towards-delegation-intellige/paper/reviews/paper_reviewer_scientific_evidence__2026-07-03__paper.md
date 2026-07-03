---
action_items:
- id: fc7c5153839b
  severity: science
  text: Section 4.2 (Main Results) and Table 1 lack statistical significance testing.
    The margin between SearchSwarm (68.1) and MiroThinker (67.9) on BrowseComp is
    0.2 points. Without reported standard deviations, confidence intervals, or p-values
    from multiple runs, it is impossible to determine if this is a genuine improvement
    or noise.
- id: 9717be1b978a
  severity: science
  text: The ablation study in Section 4.3 ('Effectiveness of the Harness') uses a
    200-question subset but does not specify if this subset is a random sample or
    a curated hard/easy set. If not random, the +10.0 gain may be biased. Please clarify
    the sampling methodology or provide results on the full benchmark.
- id: 20fb773f63ff
  severity: science
  text: The claim that SearchSwarm 'exceeds GPT-5.2-Thinking' (Section 4.2) relies
    on a single-point comparison (68.1 vs 65.8) without error bars. Given the proprietary
    nature of the baseline, the authors must explicitly state the variance of their
    own model's performance across seeds to validate the robustness of this claim.
artifact_hash: 23164a835e9fc14f10b36f04bd2aeba4213e5a3b759192c46a449dbfe25b61f3
artifact_path: projects/PROJ-689-searchswarm-towards-delegation-intellige/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T17:14:14.411889Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling architecture for "delegation intelligence" and reports strong performance gains on deep research benchmarks. However, the scientific evidence supporting the magnitude and robustness of these claims is currently insufficient due to a lack of statistical rigor.

The primary concern lies in the reporting of quantitative results in Section 4.2 and Table 1. The authors claim SearchSwarm achieves state-of-the-art results among lightweight models, citing specific margins (e.g., 68.1 vs. 67.9 on BrowseComp). In the absence of reported standard deviations, confidence intervals, or results from multiple random seeds, these point estimates are scientifically weak. A 0.2-point difference is well within the noise floor of typical LLM evaluation pipelines. Without statistical significance testing (e.g., t-tests or bootstrap confidence intervals), the claim that SearchSwarm strictly outperforms MiroThinker is not empirically supported.

Furthermore, the ablation study in Section 4.3 relies on a 200-question subset of BrowseComp to demonstrate the harness's effectiveness (+10.0 gain). The manuscript does not specify the sampling strategy for this subset. If the subset was not randomly selected, the results may suffer from selection bias, inflating the perceived impact of the method. To ensure the evidence is robust, the authors must clarify the sampling method or, preferably, report ablation results on the full benchmark with variance metrics.

Finally, the comparison against closed-source models (e.g., GPT-5.2-Thinking) is presented as a definitive superiority claim. While the point estimate is higher, the lack of error bars on the authors' own results makes it difficult to assess the reliability of this advantage. The paper should include a discussion on the statistical significance of these gains or explicitly frame them as preliminary observations pending further variance analysis.
