---
action_items:
- id: 16d5477a6b62
  severity: science
  text: Report standard errors or 95% confidence intervals for all success rate metrics
    in Tables 1 and 2 to quantify uncertainty.
- id: d71a9a046a43
  severity: science
  text: Apply multiple-comparison correction (e.g., Bonferroni or FDR) across the
    6 models and 4 benchmarks tested, or justify its omission.
- id: 13ca6fe7ab8a
  severity: science
  text: Provide sample sizes (N) for each cell in result tables and include error
    bars in ablation figures (Figure 2).
artifact_hash: d1f8365f26381f8307ae3c2777500a8f5e24701d5ef1d5e42dce305039a248a5
artifact_path: projects/PROJ-599-mmskills-towards-multimodal-skills-for-g/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-02T20:27:52.094761Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical reporting in the Experiments section lacks necessary rigor for the claims made. Specifically, Tables 1 and 2 report point estimates for success rates (e.g., 50.11% vs 44.08% in Table 1, lines 100-130) without confidence intervals, standard errors, or p-values. Given the stochastic nature of LLM agents and the benchmark environments, variance is expected. Without uncertainty quantification, it is unclear if observed improvements are statistically significant or due to random fluctuation.

Furthermore, the study conducts multiple comparisons across six model families, four benchmarks, and numerous application domains (Table 1). There is no mention of correction for multiple hypothesis testing (e.g., Bonferroni or FDR). With 6 models × 3 conditions × 4 benchmarks, the family-wise error rate is high, increasing the risk of false positives.

Sample sizes vary significantly across domains (e.g., VLC has 17 tasks in Table 1, while Chrome has 45). Small sample sizes reduce statistical power and increase the risk of Type II errors, yet no power analysis or confidence intervals are provided to contextualize these results.

Finally, the ablation studies in Figure 2 present percentage-point gains without error bars. To support the claim that 'State cards and multi-view visual evidence both improve skill utility,' significance testing or bootstrapped confidence intervals are required.

Additionally, for reproducibility, the raw logs of success/failure per task should be made available to allow independent verification of variance calculations. The Appendix provides skill source statistics but not the evaluation run variance. Please add standard errors or 95% confidence intervals to all result tables. Apply a multiple-comparison correction method or justify why it is omitted. Report sample sizes (N) clearly for each cell.
