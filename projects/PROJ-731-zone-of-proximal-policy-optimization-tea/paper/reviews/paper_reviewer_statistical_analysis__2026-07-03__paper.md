---
action_items:
- id: 44e99b40c8d6
  severity: science
  text: The cluster bootstrap (Sec. 5.6) resamples benchmarks to assess macro-average
    robustness but does not account for run-to-run variance. Given the small number
    of training runs (implied n=1 per method/scale), the authors should clarify if
    the reported CIs underestimate total uncertainty or provide a justification for
    treating the single run as representative.
- id: 95210cd7cfd3
  severity: science
  text: In the BCQ/NCQ audit (Tab. 14-15), the 'match-neg' metric for NCQ at 0.8B
    is 82.7%. The text attributes this to 'limited capacity,' but the statistical
    significance of this scale-dependent drop (from 82.7% to 0.2%) is not tested.
    A formal test (e.g., chi-square or Fisher's exact) comparing match-neg rates across
    scales is needed to support the claim of a 'collapse'.
- id: b3b3f932289c
  severity: science
  text: The ablation study (Tab. 11) reports point estimates for component contributions
    (BCQ vs. NCQ) without confidence intervals. Given the super-additive claim, the
    authors should provide error bars or statistical tests to confirm the interaction
    effect is not due to random fluctuation in benchmark selection.
artifact_hash: 0fd8fa2b8ede4e304df4503c08bd0823fb3038495b7a89b759c4ee4216df60db
artifact_path: projects/PROJ-731-zone-of-proximal-policy-optimization-tea/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T03:39:57.189530Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in the paper is generally rigorous in its use of benchmark-level cluster bootstrapping to establish the robustness of macro-average gains (Sec. 5.6, Tabs. 12-13). The authors correctly identify that benchmark selection is a primary source of variance in LLM evaluation and address it by resampling benchmarks 10,000 times. The resulting 95% CIs effectively demonstrate that the ZPPO improvements over baselines (GRPO†, Off-Distill) are not artifacts of a specific benchmark subset, as the intervals exclude zero in nearly all cases.

However, there are three specific areas where the statistical treatment requires clarification or strengthening:

1.  **Run-to-Run Variance vs. Benchmark Variance:** The cluster bootstrap (Sec. 5.6) explicitly quantifies uncertainty due to *which* benchmarks are included in the average. However, the paper appears to report results from a single training run per configuration (implied by the lack of "mean ± std" notation in the main tables). In RL, training dynamics can be highly sensitive to initialization and sampling noise. By only bootstrapping the benchmarks, the reported CIs may underestimate the total uncertainty if the single run is an outlier. The authors should either report multiple seeds (e.g., n=3) to estimate run-to-run variance or explicitly state that the single-run results are representative and that the benchmark bootstrap is the only source of reported uncertainty.

2.  **Statistical Significance of Scale-Dependent Effects:** In the BCQ/NCQ audit (Sec. 5.7, Tabs. 14-15), the authors observe a dramatic drop in "match-neg" (repeating a wrong answer) for the NCQ task as model scale increases (82.7% at 0.8B vs. 0.2% at 9B). While the trend is clear, the paper treats these as descriptive statistics. To support the claim that this is a genuine "collapse" of the failure mode rather than random variation, a formal statistical test (e.g., Fisher's exact test or a chi-square test for trend) comparing the match-neg rates across the four scales should be included.

3.  **Uncertainty in Ablation Interactions:** The central claim of "super-additivity" (ZPPO > BCQ + NCQ + Buffer) relies on the difference between the full method and the sum of its parts (Tab. 11). The table presents only point estimates. Given the magnitude of the gains, it is crucial to know if the interaction term is statistically significant. Providing confidence intervals for the ablation differences or conducting a test for the interaction effect would strengthen the evidence for the super-additive claim.

Overall, the use of benchmark bootstrapping is a strong methodological choice, but the lack of run-level variance estimation and formal significance testing for the component audits leaves some statistical gaps.
