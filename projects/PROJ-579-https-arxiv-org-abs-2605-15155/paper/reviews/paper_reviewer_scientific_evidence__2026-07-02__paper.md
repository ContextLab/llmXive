---
action_items:
- id: 2e4f16ccb244
  severity: science
  text: Report standard deviation or confidence intervals for all main results in
    Table 1. The paper claims substantial improvements (e.g., +9.4% on ALFWorld) but
    provides no measure of variance across seeds or runs, making statistical significance
    impossible to assess.
- id: dcfc80c96e57
  severity: science
  text: Clarify the sample size (number of random seeds) used for the main experiments.
    The 'Implementation Details' section mentions GPU count and batch sizes but omits
    the number of independent training runs, which is critical for evaluating the
    robustness of the reported gains.
- id: f8bfe30d6ed4
  severity: science
  text: Provide effect size metrics (e.g., Cohen's d) or statistical test results
    (p-values) when comparing SDAR against baselines like GRPO and Skill-SD. The current
    reliance on point estimates in Table 1 is insufficient to rule out random fluctuation
    as the cause of observed differences.
artifact_hash: a2fe5096ad1b93f50db064c40f59b84672b255d5a406d9c082d97d449a5f037d
artifact_path: projects/PROJ-579-https-arxiv-org-abs-2605-15155/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:53:27.456517Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a novel method (SDAR) for stabilizing On-Policy Self-Distillation in multi-turn agents. The core scientific claim—that a sigmoid-gated auxiliary loss can prevent the instability of naive distillation while improving performance—is supported by a coherent theoretical framework and extensive empirical results across three benchmarks. The ablation studies (Figures 5-8) effectively isolate the contribution of the gating mechanism, hyperparameters, and loss type, demonstrating that the proposed design choices are not arbitrary.

However, the strength of the scientific evidence is currently limited by a lack of statistical rigor in the reporting of results. Table 1 (tables/experiment.tex) presents mean performance metrics (e.g., 84.4% vs. 75.0% on ALFWorld) without any indication of variance. In reinforcement learning, where training dynamics can be highly stochastic, reporting results from a single run or without standard deviations makes it impossible to determine if the observed improvements are statistically significant or merely artifacts of random initialization or environment stochasticity. The "Implementation Details" section (lines 330-345) specifies hardware and batch sizes but fails to state the number of random seeds used for each experiment.

Furthermore, while the paper claims "substantial improvements" and "consistent gains," it does not provide p-values, confidence intervals, or effect sizes to substantiate these claims against the baselines. For instance, the difference between SDAR and GRPO+OPSD on Qwen2.5-7B in ALFWorld (85.9% vs. 80.4%) appears significant, but without variance data, this remains an unverified assertion. The robustness analysis (Table 2) shows gains across retrieval strategies, but again, lacks error bars to confirm that the performance drop with "Random Retrieval" is not within the noise floor of the baseline.

To meet the standards of scientific evidence required for acceptance, the authors must re-run experiments with multiple seeds (typically 3-5) and report mean ± standard deviation for all primary metrics. Additionally, statistical significance tests (e.g., t-tests or Wilcoxon signed-rank tests) should be performed to validate that the proposed method outperforms the baselines with high confidence. Without these additions, the magnitude of the claimed improvements remains scientifically ambiguous.
