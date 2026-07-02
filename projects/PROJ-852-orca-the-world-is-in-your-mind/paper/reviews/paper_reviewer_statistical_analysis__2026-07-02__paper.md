---
action_items:
- id: 448e6e091214
  severity: science
  text: The ablation study (Table 4) reports single-point averages for complex downstream
    tasks (Text, Image, Action) without standard deviations, confidence intervals,
    or significance testing. Given the high variance in LLM benchmarks, claim 'All
    three objectives provide the most balanced downstream readouts' is statistically
    unsupported without error bars or p-values.
- id: b67586c4a87e
  severity: science
  text: The real-robot evaluation (Table 3) uses a rule-based scoring system with
    integer points. The paper reports mean scores (e.g., 36.6 vs 31.2) but omits the
    number of independent trials (N) per task and model, and lacks statistical tests
    (e.g., t-test, Mann-Whitney U) to confirm if the observed differences are significant
    or due to random variance in robot execution.
- id: 4af74d719d06
  severity: science
  text: The image prediction benchmark (Table 2) relies on LLM judges (Gemini, GPT-5.4)
    scoring on a 1-5 scale. The paper reports mean and standard deviation but does
    not address inter-rater reliability (e.g., Cohen's Kappa) or the potential bias
    of using proprietary models as ground truth, which undermines the statistical
    validity of the '59.8' score claim.
artifact_hash: b5c260e3cad57a502ee5de9a92837ef2e2204625255c1d5da0b8c81a30982bbf
artifact_path: projects/PROJ-852-orca-the-world-is-in-your-mind/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T19:18:52.767945Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: full_revision
---

The statistical rigor of the evaluation section is insufficient to support the paper's central claims regarding the superiority of the Orca paradigm.

First, the **ablation study** (Section 5.3, Table 4) presents a critical statistical flaw. The authors report single-point average scores for Text, Image, and Action generation across different loss configurations. For complex generative tasks, especially those involving LLMs and robotics, performance is inherently stochastic. Reporting only the mean without standard deviations, confidence intervals, or results from multiple random seeds makes it impossible to determine if the observed improvements (e.g., the jump from 42.6 to 48.0 average) are statistically significant or merely noise. The claim that the joint objective is "most balanced" is qualitative; a quantitative statistical test (e.g., ANOVA or paired t-tests) is required to validate this.

Second, the **real-robot evaluation** (Section 5.2.3, Table 3) lacks essential experimental design details. The rule-based scores (e.g., Orca-4B achieving 36.6 vs. $\pi_{0.5}$'s 31.2) are presented as definitive metrics. However, the manuscript does not specify the number of independent trials ($N$) conducted for each task and model configuration. Without $N$, the calculation of standard error is impossible. Furthermore, no statistical significance tests (such as a Mann-Whitney U test, which is appropriate for ordinal/ranked scores) are reported to confirm that the difference between Orca and the baselines is not due to chance. In robotics, where execution variance is high, a difference of ~5 points on a 100-point scale may not be significant without rigorous testing.

Third, the **image prediction benchmark** (Section 5.2.2, Table 2) relies entirely on LLM judges (Gemini 3.1 Pro, GPT 5.4, etc.) for scoring. While the authors report mean and standard deviation, they fail to address **inter-rater reliability**. When using multiple LLMs as judges, it is crucial to demonstrate that these judges agree with each other (e.g., via Cohen's Kappa or Kendall's W). If the judges are inconsistent, the reported "average" score is statistically meaningless. Additionally, the use of proprietary models as the ground truth for a scientific benchmark introduces potential bias that is not statistically controlled for.

Finally, the **scaling laws** (Section 5.1, Figures 1 & 2) are presented as smooth curves. While the trend is visually apparent, the paper does not provide the underlying data points, error bars for the loss values, or a fitted model with confidence intervals. This makes it difficult to assess the robustness of the claimed "scalability."

To proceed, the authors must re-run evaluations with sufficient trials to calculate confidence intervals, perform statistical significance testing on all comparative results, and report inter-rater reliability for LLM-based metrics.
