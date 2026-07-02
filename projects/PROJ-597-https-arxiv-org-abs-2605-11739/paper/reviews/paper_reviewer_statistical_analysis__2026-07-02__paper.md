---
action_items:
- id: ca6babf5cc82
  severity: science
  text: The paper reports performance gains and acceleration factors (e.g., 3x speedup)
    across multiple benchmarks but lacks statistical significance testing. The Checklist
    (Item 7) admits no error bars or significance tests were performed. Authors must
    report standard deviations or confidence intervals over multiple random seeds
    for the main efficiency claims to rule out variance-driven results.
- id: bdd47f1a9222
  severity: science
  text: The subspace alignment analysis (Section 3.3, Fig 4b) and spectral metrics
    (Table 1) are presented as single deterministic values derived from specific training
    runs. Without reporting variance across seeds or multiple runs, the claim that
    OPD 'consistently' exhibits stronger low-rank concentration is statistically unsupported.
    Please provide error bars or aggregate statistics.
- id: d0b834671d9c
  severity: science
  text: The validation set for EffOPD (Section 4.1) is described as a 'random sample
    of 50 examples.' The statistical power of such a small sample to reliably detect
    performance degradation during extrapolation is unclear. Authors should justify
    the sample size or report the variance of the validation metric to ensure the
    extrapolation decisions are robust.
artifact_hash: 86f3dbb1aa547b2619e2d0068122fd6e86cb21c5f6980bdd3810b1ffe64d94e9
artifact_path: projects/PROJ-597-https-arxiv-org-abs-2605-11739/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:59:14.289728Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents a compelling empirical analysis of On-Policy Distillation (OPD) versus Reinforcement Learning (RL), focusing on parameter update dynamics. However, from a statistical analysis perspective, the evidence supporting the central claims of "consistent" efficiency and "early" stabilization is currently insufficient due to a lack of variance reporting.

First, the primary quantitative claims regarding the $3\times$ acceleration and superior reasoning gains (Section 4.2, Figure 5) are presented as point estimates. The NeurIPS Checklist (Item 7) explicitly states that no error bars or statistical significance tests were included. In deep learning experiments, performance can vary significantly based on random seeds, initialization, and data shuffling. Without reporting standard deviations or confidence intervals over multiple independent runs, it is impossible to determine if the observed differences between OPD and RL, or the gains from EffOPD, are statistically significant or merely artifacts of specific random seeds. The claim that OPD "consistently" outperforms RL requires evidence of this consistency across stochastic variations.

Second, the geometric analysis in Section 3 (Table 1 and Figure 4) relies on metrics like Effective Rank and Subspace Alignment. These are reported as single scalar values for each model scale. Given that training dynamics are stochastic, these metrics should be aggregated over multiple runs to establish their stability. The current presentation treats the training trajectory as deterministic, which is a strong assumption not supported by the data provided.

Finally, the EffOPD method relies on a lightweight validation set of only 50 examples (Section 4.1) to make extrapolation decisions. The statistical reliability of a decision based on such a small sample size is questionable. The variance of the validation metric on 50 samples could be high, potentially leading to unstable extrapolation steps. The authors should either increase the validation set size, report the variance of the validation scores, or provide a theoretical justification for why 50 samples are sufficient to make robust optimization decisions.

To strengthen the paper, the authors must re-run key experiments with multiple seeds, report mean and standard deviation (or 95% confidence intervals) for all performance and geometric metrics, and perform statistical significance tests (e.g., t-tests) to validate the superiority of OPD and EffOPD.
