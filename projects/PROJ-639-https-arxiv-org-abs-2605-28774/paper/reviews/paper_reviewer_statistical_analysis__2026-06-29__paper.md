---
action_items:
- id: 21d045e15d9f
  severity: science
  text: Report variance across multiple training seeds to validate statistical significance
    of AXPO vs GRPO improvements, as evaluation std alone is insufficient.
- id: 85b5467c0d4d
  severity: science
  text: Address multiple-comparison issues across 9 benchmarks x 4 sizes x 2 metrics
    (72 tests) via correction or explicit discussion of false positive risk.
- id: 9c5879259d6c
  severity: writing
  text: Report 95% confidence intervals for main Pass@1/4 results derived from training
    seeds, not just evaluation rollouts.
artifact_hash: c3a0cadd7f6fad4530caf3425af37b062e581bf6756717caa2b10b397e7c3c2b
artifact_path: projects/PROJ-639-https-arxiv-org-abs-2605-28774/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T10:48:54.750722Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical validation of the reported improvements requires strengthening to support the central claims. Section 3.1 and Appendix A.3 report standard deviation across four independent evaluation rollouts (see `tables/tab_main_p1_std.tex`). This quantifies evaluation noise, not training instability. The claim in Appendix A.3 that "headline gains lie above the per-rollout noise floor" is statistically invalid for comparing two different training recipes (AXPO vs GRPO), as it conflates evaluation variance with training variance. To validate the significance of the reported improvements (e.g., +1.8 pp at 8B), variance across multiple training seeds is required. Without this, a t-test cannot be performed, and the observed gains may be due to random initialization effects.

Section 3.2 presents results across 9 benchmarks, 4 model sizes, and 2 metrics, resulting in 72 comparisons. No multiple-comparison correction (e.g., Bonferroni, FDR) is applied. Several individual benchmark deltas are negative (e.g., 4B Math-VR Pass@1: -0.2 in `tables/tab_main_p1_mathvr.tex`), suggesting the average gain may not be uniform across all tasks. The authors should either apply a correction or explicitly discuss the robustness of the average gain against the risk of false positives.

Finally, confidence intervals for the main results are not reported. Standard errors should be derived from training seeds, not just evaluation rollouts. Reporting 95% confidence intervals for the Pass@1 and Pass@4 averages would provide a clearer picture of the uncertainty and allow readers to assess the reliability of the improvements. The current reliance on evaluation std to justify training improvements is a methodological flaw that must be addressed.
