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
reviewed_at: '2026-06-09T04:36:33.297435Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: full_revision
---

This re-review finds that neither of the prior statistical analysis action items has been adequately addressed in the current revision.

First, regarding confidence intervals (Action Item `eaf992545185`): Table 1 (`tables/main_table.tex`) continues to report point estimates for Source Selection Accuracy, Retrieval Accuracy, and LLM-as-a-Judge metrics without any variance estimates (e.g., confidence intervals or standard deviations). The Appendix Implementation Details (`sections/8_appendix.tex`, Section "Implementation Details") explicitly states: "We use a sampling temperature of 0.0 ... which makes the predictions deterministic, so all reported numbers come from a single run per configuration." Consequently, there is no empirical basis for variance estimation without re-running experiments with stochastic sampling or bootstrapping the test set. The lack of confidence intervals undermines the reliability of the reported gains (e.g., 68.58% vs 64.88% in Table 1).

Second, regarding multiple comparisons (Action Item `1ff2bf25f24c`): The ablation studies in Section 6 (`sections/6_experimental_result.tex`), specifically Figures 3-5 (`figures/topk_sweep.tex`, `figures/qwen_scaling.tex`, `figures/cross_backbone_selector.tex`), sweep hyperparameters ($k$) and backbone scales. The text describes trends (e.g., "improves monotonically", "clear lead") but provides no statistical significance testing (e.g., t-tests, ANOVA) or corrections for multiple comparisons (e.g., Bonferroni). Given the multiple backbones and configurations evaluated, the risk of Type I error is unaddressed.

To proceed, the authors must either (1) re-run experiments with stochastic temperature settings to enable variance estimation, or (2) apply test-set bootstrapping to generate confidence intervals for Table 1. Additionally, statistical significance tests must be applied to the ablation study comparisons to validate the observed performance differences.
