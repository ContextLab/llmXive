---
action_items:
- id: ba34e20f79d8
  severity: science
  text: "Provide confidence intervals (e.g., 95% CI) for all reported Pearson correlations\
    \ (r=0.823, 0.801, etc.) and for mean consensus\u2011gain values across mediators\
    \ and conditions."
- id: f8f156ee9384
  severity: science
  text: "Clarify the statistical testing framework used to compare mediators (e.g.,\
    \ ANOVA, mixed\u2011effects models) and report corresponding p\u2011values, effect\
    \ sizes, and multiple\u2011comparison corrections (e.g., Bonferroni, Holm)."
- id: f544eaa9c337
  severity: science
  text: "Specify the assumptions underlying Pearson correlation (linearity, normality)\
    \ and, if violated, present alternative non\u2011parametric analyses (Spearman\u2019\
    s \u03C1) or transform the data."
- id: 7a23e1eab332
  severity: science
  text: "Report the variance (standard deviation or standard error) for consensus\u2011\
    gain, intervention timeliness, and effectiveness for each mediator; include statistical\
    \ tests for differences between proprietary and open\u2011source models."
- id: 6eb4c8f9a87e
  severity: science
  text: Detail the random seeds, temperature settings, and any stochastic sampling
    procedures used in scenario generation, simulation, and evaluation to enable exact
    replication.
- id: 0cc877592085
  severity: writing
  text: Address the handling of edge cases in the Consensus Gain formula (division
    by zero when S_unmed=1) and justify the alternative reporting method.
- id: 6ec253b6c945
  severity: science
  text: "Explain how Krippendorff\u2019s \u03B1 values were computed (e.g., number\
    \ of annotators, bootstrap CI) and provide confidence intervals for these reliability\
    \ metrics."
- id: 880e1fcd37ab
  severity: science
  text: "Consider evaluating inter\u2011rater reliability for the automatic evaluator\
    \ by using multiple LLM backbones and reporting agreement statistics across them."
artifact_hash: 85696f027c2296857479727071f7c34ef0cc40db782dc072c038e2773b79f464
artifact_path: projects/PROJ-680-socrates-towards-reliable-automated-eval/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T00:48:04.398483Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript introduces the SoCRATES benchmark and proposes three novel metrics—Consensus Gain, Intervention Timeliness, and Intervention Effectiveness—to evaluate proactive LLM mediators. While the conceptual design is compelling, the statistical analysis lacks rigor in several key areas.

**Correlation reporting:** The authors cite Pearson r values (e.g., 0.823, 0.801) to demonstrate alignment between the topic‑localized evaluator and expert annotations, yet no confidence intervals or hypothesis‑testing details are provided. Pearson correlation assumes linearity and approximately normal distributions of the paired scores; these assumptions are not examined, nor are alternative non‑parametric correlations reported when assumptions may be violated.

**Comparative analyses across mediators and conditions:** The study aggregates results over 4 800 runs (8 mediators × 40 scenarios × 15 conditions) and presents mean Consensus Gain values per mediator and per domain. However, there is no statistical testing to assess whether observed differences are significant. Given the large number of pairwise comparisons (e.g., 8 × 8 domain‑mediator cells, plus axis‑specific shifts), a multiple‑comparison correction (Bonferroni, Holm, or false‑discovery‑rate) is essential to control Type I error. Reporting only averages without standard errors or confidence intervals obscures the variability evident in Table 7 (median ± half‑range) and impedes inference about “top‑tier” versus “bottom‑tier” performance.

**Variance and effect‑size quantification:** The manuscript includes some variance summaries (e.g., median ± half‑range), but these are not integrated into formal statistical tests. Effect sizes (Cohen’s d or η²) for differences between proprietary and open‑source models, or across socio‑cognitive axes, would strengthen claims about the impact of model scale versus architecture.

**Metric definition edge cases:** The Consensus Gain formula divides by (1 − S_unmed). When S_unmed = 1, the authors switch to reporting S_med − S_unmed, but the rationale and statistical handling of this boundary case are not discussed. Similarly, Intervention Timeliness can yield negative values if the intervention occurs after the window; the paper does not describe whether such values are truncated or retained, nor how they affect aggregate scores.

**Reliability of annotations:** Krippendorff’s α is reported for simulation fidelity (α = 0.75) and expert annotation (α = 0.86), yet no confidence intervals or bootstrap analyses are provided. Knowing the precision of these reliability estimates is important for interpreting downstream correlations.

**Reproducibility of stochastic components:** The benchmark relies on multiple stochastic pipelines (seed scenario search, LLM‑based scenario writing, simulation‑based filtering, and the automatic evaluator). Random seeds, temperature settings, and sampling strategies are mentioned only cursorily (e.g., “temperature 0.6” for mediators). Full reproducibility requires explicit documentation of all random seeds and any non‑deterministic API calls, as well as versioning of the LLM backbones used.

**Evaluator backbone robustness:** The authors demonstrate that switching the evaluator backbone from DeepSeek‑V3.2 to Qwen3‑235B yields similar Pearson correlations, but they do not conduct statistical tests to confirm that performance differences are insignificant. A paired‑sample test across the same dialogues would substantiate the claim of backbone‑agnostic evaluation.

**Statistical power considerations:** No power analysis is presented to justify the number of scenarios, conditions, or runs per mediator. While the total number of trajectories is large, the effective sample size for each condition‑mediator pair may be limited (e.g., only five base scenarios per domain). Power calculations would clarify whether the study is sufficiently powered to detect modest performance differences.

In summary, the benchmark and metrics are promising, but the statistical methodology must be expanded to include proper inference, assumption checking, variance reporting, and reproducibility details. Addressing the action items above will substantially improve the paper’s credibility and utility for the community.
