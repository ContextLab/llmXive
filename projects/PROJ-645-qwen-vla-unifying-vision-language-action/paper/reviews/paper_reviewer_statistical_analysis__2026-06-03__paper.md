---
action_items:
- id: 6c8c784ad918
  severity: science
  text: "Provide measures of variability (e.g., standard deviations, confidence intervals)\
    \ for all reported success rates in Tables\u202F1\u20115 and any other quantitative\
    \ results."
- id: 2be3464c8b42
  severity: science
  text: "Perform and report statistical significance tests (e.g., paired t\u2011tests,\
    \ Wilcoxon signed\u2011rank tests) when comparing Qwen\u2011VLA variants against\
    \ baselines to substantiate claims of superiority."
- id: 6e1acb80a1ab
  severity: science
  text: "Address multiple\u2011comparison issues arising from evaluating on many benchmarks\
    \ (LIBERO, RoboCasa\u2011GR1, Simpler\u2011WidowX, RoboTwin, R2R, RxR, DOMINO,\
    \ OOD tasks). Apply appropriate corrections (e.g., Bonferroni, Holm) or clearly\
    \ state that each metric is considered independently."
- id: e6dd659cfb96
  severity: science
  text: Report the number of random seeds used for each experiment and include seed
    values; provide variance across seeds to demonstrate robustness.
- id: 89c47031e0e6
  severity: science
  text: "Detail the hyper\u2011parameter search strategy for PPO (learning rates,\
    \ clipping \u03B5, GAE \u03BB) and include sensitivity analyses to show that performance\
    \ is not contingent on a single lucky configuration."
- id: d84d3910b895
  severity: writing
  text: 'Include a reproducibility checklist: exact dataset splits, preprocessing
    pipelines, and versioned code for the DiT action decoder and RLinf framework.'
artifact_hash: 4317c2f95ff2f77ca9da4f22e56217afc73d1946ecdbafc6b1dfd103e809ccd5
artifact_path: projects/PROJ-645-qwen-vla-unifying-vision-language-action/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-03T04:48:02.217604Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents an ambitious unified vision‑language‑action model and reports impressive raw success rates across a wide suite of manipulation, navigation, and dynamic‑manipulation benchmarks. However, from a statistical‑analysis standpoint the evidence is under‑specified, limiting confidence in the claimed improvements.

1. **Absence of variability estimates** – All quantitative results (e.g., Table 1 “Robot manipulation results across benchmarks”, Table 2 “Real‑world in‑domain performance”, Table 3 “OOD performance”, Table 4 “VLN‑CE comparison”, Table 5 “DOMINO results”) are reported as single point percentages without any indication of variance. The paper does not state how many random seeds or independent training runs were performed, nor does it provide standard deviations or confidence intervals. Consequently, it is impossible to assess whether observed differences (e.g., Qwen‑VLA‑Instruct’s 97.9 % vs. ABot‑M0’s 98.6 % on LIBERO) are statistically meaningful or could arise from stochastic training variability.

2. **Lack of hypothesis testing** – The authors frequently claim “outperforms” or “surpasses” baselines, yet no statistical tests are presented to support these statements. For paired comparisons (same data splits, same hardware), a paired t‑test or non‑parametric alternative should be employed, and resulting p‑values reported. This is especially critical for modest gains (e.g., +4.9 pp on RoboCasa‑GR1) where random fluctuations could explain the difference.

3. **Multiple‑comparison concerns** – The paper evaluates on at least eight distinct benchmarks, each with several metrics (success, OSR, SPL, etc.). Conducting separate significance tests on each metric inflates the family‑wise error rate. The authors should either apply a correction method (Bonferroni, Holm‑Šidák) or pre‑register a primary metric and treat others as exploratory.

4. **Reinforcement‑learning hyperparameter sensitivity** – Section 4.2 (RL) describes a PPO implementation with specific ε, γ, λ values, but no sensitivity analysis is provided. Since PPO performance can be highly dependent on these settings, reporting results across a grid of hyperparameters or at least confirming stability across a few seeds would strengthen the claim that the RL fine‑tuning genuinely improves task success.

5. **Dataset size and sampling details** – While the paper lists percentages of each data source (e.g., “6.0 % egocentric human data”), it does not give absolute numbers of trajectories, episodes, or frames per benchmark. Without these counts, readers cannot gauge whether the sample sizes are sufficient for reliable estimation of success rates, nor can they reproduce the data splits.

6. **Reproducibility checklist** – The manuscript would benefit from a concise reproducibility section (or checklist) that enumerates random seeds, software versions (PyTorch, CUDA), and exact preprocessing steps for each dataset (e.g., how action trajectories are down‑sampled to 50 Hz). Providing the full training scripts and a deterministic evaluation pipeline is essential for the community to verify the reported numbers.

In summary, the empirical claims are promising but lack the statistical rigor required to substantiate superiority claims. Addressing the points above (variability reporting, hypothesis testing, multiple‑comparison control, hyperparameter sensitivity, dataset statistics, and reproducibility details) would markedly improve the paper’s scientific credibility.
