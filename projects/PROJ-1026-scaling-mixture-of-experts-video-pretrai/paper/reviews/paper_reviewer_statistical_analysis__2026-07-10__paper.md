---
action_items:
- id: 5ba7492168dc
  severity: writing
  text: "Table 1 (RBench) and Section 6.1 report point estimates (e.g., 0.620) for\
    \ model performance without any measure of uncertainty (standard deviation, confidence\
    \ interval, or range). Given that these scores likely derive from a finite set\
    \ of prompts (650 for RBench) and potentially stochastic generation, the absence\
    \ of variance reporting prevents assessment of result stability. Report mean \xB1\
    \ SD over multiple evaluation runs or provide 95% confidence intervals for all\
    \ benchmark scores."
- id: e7d7391c9c36
  severity: writing
  text: Section 6.3 (User Study) reports Good/Same/Bad rates based on 400 prompts
    per pair but omits statistical significance testing. Claims like 'clearly outperforms'
    or 'consistent advantage' are made without p-values or effect sizes (e.g., Cohen's
    d or odds ratios) derived from the pairwise comparisons. Apply a binomial test
    or McNemar's test to the GSB counts to determine if the observed 'Good' rates
    are statistically significant (p < 0.05) and report the effect size.
- id: 30ede8d33989
  severity: writing
  text: "Section 5.2.1 (Scaling Experiments) and Figures 3-5 present training/validation\
    \ loss curves and inference latency ratios as single deterministic lines. For\
    \ deep learning experiments involving stochastic optimization and data sampling,\
    \ these metrics should be reported with uncertainty bands (e.g., \xB11 standard\
    \ deviation over 3-5 seeds) to distinguish genuine scaling trends from random\
    \ variance. Add error bands to the loss curves and report variance for the latency\
    \ ratios."
artifact_hash: 9ee70f69980a19ab6b09b1ef85c408bba9d6c20db5c959c0faf89cac5e30112c
artifact_path: projects/PROJ-1026-scaling-mixture-of-experts-video-pretrai/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-10T03:03:03.299763Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical reporting in the evaluation and scaling sections lacks necessary measures of uncertainty and significance testing, which limits the ability to distinguish genuine performance gains from random variance.

In **Section 6.1 (Internal Benchmark)** and **Table 1 (RBench)**, the authors report precise point estimates (e.g., 0.620, 0.578) for model performance across various tasks. However, there is no accompanying measure of uncertainty, such as standard deviation (SD), standard error (SE), or confidence intervals (CI). In video generation benchmarks, scores can vary due to the stochastic nature of the diffusion process and the specific subset of prompts used. Without reporting variance (e.g., "0.620 ± 0.015 over 3 seeds"), readers cannot determine if the reported "state-of-the-art" margins are statistically robust or within the noise floor of the evaluation. This is a reporting gap that should be fixed by aggregating results from multiple evaluation runs.

In **Section 6.3 (User Study)**, the paper presents Good-Same-Bad (GSB) results based on 400 prompts per comparison pair. While the raw counts or percentages are implied, the text makes qualitative claims of superiority ("clearly outperforms," "consistent advantage") without performing or reporting a formal statistical test. For pairwise human evaluations, a binomial test or McNemar's test is standard to determine if the proportion of "Good" votes significantly exceeds the "Bad" votes (or 50% chance). Additionally, effect sizes (e.g., odds ratios) should be reported to quantify the magnitude of the improvement, rather than just stating it is "clear."

Finally, in **Section 5.2 (Scaling Experiments)**, the training loss curves (Figures 3, 4, 5) and inference latency ratios are presented as single, smooth lines. In deep learning research, it is standard practice to report these metrics with error bands (e.g., ±1 SD) across multiple random seeds (typically 3-5) to demonstrate that the observed scaling laws and efficiency gains are reproducible and not artifacts of a specific random initialization or data shuffle. The absence of these error bands makes the "predictable scaling" claim harder to verify statistically.

These issues are primarily reporting gaps (severity: writing) that can be resolved by re-analyzing existing evaluation data or re-running the evaluation scripts with multiple seeds, rather than requiring new model training.
