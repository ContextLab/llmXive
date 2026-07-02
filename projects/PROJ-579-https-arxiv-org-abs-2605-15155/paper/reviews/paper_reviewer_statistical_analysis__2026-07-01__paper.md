---
action_items:
- id: a42ba13bb26e
  severity: science
  text: The paper reports point estimates (e.g., +9.4% on ALFWorld) without any measure
    of statistical uncertainty. For all main results in Table 1 and ablation studies,
    report standard deviations or 95% confidence intervals derived from multiple independent
    runs (e.g., 3-5 seeds) to distinguish signal from noise.
- id: 989eddd3dfd8
  severity: science
  text: "The robustness analysis in Table 2 (retrieval strategies) presents single-run\
    \ results. Given the high variance inherent in RL training, a single run is insufficient\
    \ to claim \"graceful degradation.\" Re-run experiments with multiple seeds and\
    \ report mean \xB1 std dev to validate the statistical significance of the differences\
    \ between retrieval methods."
- id: 4c237ec56aa0
  severity: science
  text: The ablation studies for hyperparameters (Figures 4-6) lack error bars. The
    claimed "optimal" values for beta and lambda appear to be based on single trajectories.
    Provide statistical validation (e.g., confidence intervals) to ensure these hyperparameters
    are robust and not overfit to a specific random seed.
- id: 8046068008d9
  severity: science
  text: The claim that "negative-gap tokens exceed 50%" (Section 1, Observation 2)
    is a statistical assertion. The paper must explicitly state the sample size (number
    of tokens/trajectories) used for this analysis and provide the standard error
    or confidence interval for this proportion to support the magnitude of the problem.
artifact_hash: a2fe5096ad1b93f50db064c40f59b84672b255d5a406d9c082d97d449a5f037d
artifact_path: projects/PROJ-579-https-arxiv-org-abs-2605-15155/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:59:21.135218Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: full_revision
---

The statistical rigor of the experimental evaluation is currently insufficient to support the paper's strong claims regarding performance gains and robustness. While the methodology is sound, the evidence presented relies almost exclusively on point estimates from single experimental runs, which is a critical flaw in Reinforcement Learning research where variance is high.

First, **Table 1** (Main Results) and **Table 2** (Robustness Analysis) report only single scalar values for success rates and accuracy. There are no standard deviations, standard errors, or confidence intervals. In RL, performance can fluctuate significantly based on random seeds, initialization, and environment stochasticity. Without reporting results from at least 3-5 independent runs, it is impossible to determine if the reported improvements (e.g., +9.4% on ALFWorld) are statistically significant or merely artifacts of a favorable random seed. The claim that SDAR "consistently outperforms" baselines cannot be substantiated without statistical testing (e.g., t-tests or non-parametric equivalents) on the distribution of results.

Second, the **ablation studies** (Figures 4-6) lack error bars. The selection of hyperparameters $\beta=5.0$ and $\lambda=0.01$ is presented as definitive based on single-curve plots. Given the sensitivity of RL training to these parameters, the authors must demonstrate that these choices are robust across multiple seeds. The current presentation risks overfitting to a specific training trajectory.

Third, the **preliminary statistical claims** in the Introduction (e.g., "negative-gap tokens exceed 50%") are presented as facts without context. The paper must specify the dataset size (number of tokens/trajectories) used for this analysis and provide the margin of error. A proportion of 50% with a sample size of 100 has a much wider confidence interval than one with a sample size of 100,000, affecting the urgency of the proposed solution.

Finally, the **training dynamics** figures (Figure 3 and Appendix figures) show smooth curves that likely represent single runs. To validate the stability claims, these plots should include shaded regions representing the standard deviation across multiple seeds. The current visual evidence suggests stability that may not exist in the broader distribution of training runs.

To proceed, the authors must re-run all key experiments (Main Results, Robustness, and Ablations) with multiple random seeds, report mean ± standard deviation, and perform statistical significance tests to validate their claims.
