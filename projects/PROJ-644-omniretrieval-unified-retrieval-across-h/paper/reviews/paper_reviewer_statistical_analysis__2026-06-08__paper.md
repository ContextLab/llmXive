---
action_items:
- id: eaf992545185
  severity: science
  text: Report 95% confidence intervals for all metrics in Table 1 via bootstrapping
    over the test set, as single-run results lack variance estimates.
- id: 1ff2bf25f24c
  severity: science
  text: Address multiple comparisons in ablation studies (Figures 3-5) where $k$ and
    backbone scales are swept; justify significance or apply correction.
artifact_hash: f1ba0d06b47034bb9ae781a67854dde745b8b5c42ceeefcb523795f3179180a0
artifact_path: projects/PROJ-644-omniretrieval-unified-retrieval-across-h/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-08T07:49:43.475593Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript lacks rigorous statistical validation for its performance claims. Section 5.3 defines metrics (Source Selection Accuracy, Retrieval Accuracy, LLM-as-a-Judge) but omits uncertainty quantification. Table 1 presents point estimates without confidence intervals (CIs) or p-values, despite the claim in Section 6 that OmniRetrieval "consistently outperforms all baselines." Without statistical tests, these differences could arise from dataset bias rather than model efficacy.

Furthermore, Section 8 (Appendix Implementation Details) states: "all reported numbers come from a single run per configuration" due to temperature 0.0. While this ensures determinism, it precludes estimating variance across random seeds. Standard practice for deterministic LLM evaluations requires bootstrapping over the test set to derive CIs for accuracy metrics. The absence of this analysis undermines the reliability of the reported gains, as a single sample path cannot quantify estimation error. For instance, the 4% gain in Retrieval Accuracy (Table 1, GPT-5.4) lacks context on whether it exceeds the margin of error.

Additionally, Figures 3-5 present ablation studies sweeping $k$ (1, 3, 5, 10) and backbone scales without addressing multiple comparisons. With 5 backbones and 4 values of $k$, the risk of false positives increases. The paper treats these sweeps as exploratory but draws definitive conclusions about "monotonic improvement" without statistical backing.

To improve, the authors should:
1. Compute 95% CIs for all metrics in Table 1 via bootstrapping over the test questions (e.g., 1000 resamples).
2. Perform significance tests (e.g., bootstrap hypothesis testing) when comparing against baselines in Table 1.
3. Clarify how multiple comparisons in ablation figures are handled or adjust claims to reflect uncertainty.

These changes are necessary to substantiate the empirical claims statistically and align with community standards for reproducible NLP research.
