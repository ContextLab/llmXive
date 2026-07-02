---
action_items:
- id: d6abafacd0b2
  severity: science
  text: "Clarify the statistical basis for specific quantitative claims (e.g., '80%\
    \ of fully autonomous results fabricated' in Sec 3.4, 'novelty judgments negatively\
    \ correlate with impact (\u03C1=-0.29)' in Sec 1.4). Explicitly state sample sizes\
    \ (N), confidence intervals, or p-values where available, or qualify these as\
    \ preliminary findings if derived from small-scale studies."
- id: c03412cf2e99
  severity: science
  text: Address the risk of benchmark contamination and selection bias in the reported
    performance metrics (e.g., SWE-bench Verified >76% vs. ResearchCodeBench 37.3%).
    Discuss whether the evaluation datasets overlap with training data for the cited
    models and how this might inflate the reported 'success' rates in a way that does
    not generalize to novel research tasks.
- id: 1b620bb91ad3
  severity: science
  text: Provide a more rigorous definition of 'feasibility' and 'novelty' used in
    the cited benchmarks (e.g., IdeaBench, LiveIdeaBench). The claim that LLMs score
    >0.6 on novelty but <0.5 on feasibility lacks context on the inter-rater reliability
    of the human evaluators used to generate these ground-truth labels.
artifact_hash: 406e68578ff634bb909200355e48bd438ba9dc41c31d75ef24170dcb14dc58cd
artifact_path: projects/PROJ-602-https-arxiv-org-abs-2605-18661/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T02:51:58.113127Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The manuscript presents a comprehensive survey of the AI for Auto-Research landscape, synthesizing a vast array of systems and benchmarks. However, from a scientific evidence perspective, the review relies heavily on aggregating point estimates from disparate studies without sufficiently contextualizing the statistical robustness or methodological limitations of the underlying evidence.

A primary concern is the presentation of specific quantitative claims without accompanying measures of uncertainty or sample size context. For instance, in Section 3.4 (Coding and Experiments), the claim that "80% of fully autonomous results fabricated" is attributed to `mlrbench2025`. While this is a striking statistic, the review does not specify the sample size (N) of the benchmark tasks, the variance in results across different model architectures, or the criteria used to define "fabrication." Similarly, in Section 1.4, the correlation coefficient (ρ=-0.29) between LLM-as-Judge novelty scores and real-world impact is cited from `hindsight2026`. Without knowing the number of papers evaluated or the confidence interval of this correlation, it is difficult to assess the stability of this finding against potential outliers or small-sample noise.

Furthermore, the review aggregates performance metrics from benchmarks that may suffer from significant selection bias or data contamination. The stark contrast between SWE-bench Verified (>76% success) and ResearchCodeBench (37.3% success) is noted, but the review does not deeply analyze the extent to which the high performance on SWE-bench might be driven by training data leakage or the specific nature of the "verified" subset. In the context of scientific evidence, a survey must critically evaluate whether the reported "state-of-the-art" numbers reflect genuine capability or artifacts of benchmark design. The claim that "LLMs score >0.6 on novelty but <0.5 on feasibility" (Sec 1.4) relies on `guo2025ideabench`, but the review omits discussion on the inter-rater reliability of the human judges used to establish these feasibility scores, which is crucial for validating the "novelty-feasibility tradeoff" conclusion.

Finally, the evidence regarding "structural diversity collapse" in multi-agent systems (Sec 1.3) cites `jiang2025artificialhivemind`. The review would benefit from a brief summary of the experimental design used to detect this collapse (e.g., number of agents, diversity metrics used) to ensure the claim is not an artifact of a specific prompt configuration rather than a fundamental limitation of the architecture. Strengthening the review with these statistical and methodological details will significantly enhance the robustness of its central claims.
