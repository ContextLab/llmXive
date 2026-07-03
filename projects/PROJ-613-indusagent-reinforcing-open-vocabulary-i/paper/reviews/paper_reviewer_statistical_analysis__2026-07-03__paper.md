---
action_items:
- id: 2bec8abfd8d2
  severity: science
  text: The NeurIPS Checklist explicitly states 'No' for statistical significance
    (Item 7), justifying this by claiming the field 'doesn't require error bars.'
    This is scientifically unsound for a paper claiming SOTA performance with specific
    margins (e.g., +17.4% on MPDD). The authors must report standard deviations or
    confidence intervals derived from multiple random seeds or cross-validation folds
    to validate that these gains are not due to random initialization or data split
    variance.
- id: 0fe0c460516e
  severity: science
  text: The ablation studies (Tables 4 and 5) present single-point performance metrics
    without any measure of variance. Given the stochastic nature of RL training (GRPO)
    and SFT, the reported improvements (e.g., VisA dropping from 76.8% to 55.5% without
    SFT) need to be contextualized with statistical significance tests (e.g., paired
    t-tests or bootstrap confidence intervals) to ensure the observed effects are
    robust and reproducible.
artifact_hash: becd970ef8620fcce447156389fb0620d5149fe00a85e4d09a2c8efc9340b659
artifact_path: projects/PROJ-613-indusagent-reinforcing-open-vocabulary-i/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T18:22:51.661782Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents a novel agentic framework for industrial anomaly detection but lacks essential statistical rigor required to substantiate its claims of state-of-the-art performance. While the authors provide extensive point estimates in Tables 1, 2, 4, and 5, they fail to report any measure of uncertainty, such as standard deviations, confidence intervals, or p-values.

Specifically, in the "NeurIPS Paper Checklist" (Section e002), the authors explicitly answer "No" to the requirement for "Experimental result statistical significance," justifying this by stating that the field "doesn't require error bars." This justification is insufficient for a paper claiming significant performance improvements (e.g., a 17.4% increase in Anomaly Recall on MPDD). In machine learning research, particularly with stochastic training procedures like Reinforcement Learning (GRPO) and Supervised Fine-Tuning, single-run results are prone to variance based on random seeds and data splits. Without reporting results averaged over multiple independent runs (e.g., 3-5 seeds) with standard deviations, it is impossible to determine if the reported gains are statistically significant or merely artifacts of a favorable random initialization.

Furthermore, the ablation studies in Section 4.3 (Tables 4 and 5) rely entirely on single-point comparisons. The dramatic performance drops observed when removing components (e.g., the drop to 55.5% on VisA without SFT) are compelling but lack statistical validation. The authors should re-run their experiments with multiple seeds to provide mean ± std. dev. metrics. Additionally, they should perform appropriate statistical significance tests (e.g., paired t-tests or Wilcoxon signed-rank tests) when comparing their method against baselines to rigorously support their claims of superiority. The current presentation of data, while numerically impressive, does not meet the standard of statistical evidence required for a robust scientific conclusion.
