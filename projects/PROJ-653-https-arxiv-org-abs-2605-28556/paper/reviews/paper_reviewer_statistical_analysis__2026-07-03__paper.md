---
action_items:
- id: 2b0493423038
  severity: science
  text: Table 1 and Section 5 report point estimates for agent performance without
    confidence intervals or standard errors. Given the stochastic nature of LLM outputs
    and the single-run evaluation per task, statistical significance of the reported
    performance drops (e.g., -52.8%) cannot be assessed. Please add error bars (e.g.,
    via bootstrapping over tasks or multiple seeds) or explicitly state the limitation
    regarding statistical significance in the checklist and text.
- id: 73092e161200
  severity: science
  text: 'The NeurIPS Checklist (Item 7) explicitly states ''Answer: No'' for statistical
    significance due to API costs. However, the paper makes strong comparative claims
    (e.g., ''severe drops'') based on single-point estimates. To support these claims
    scientifically, the authors must either provide variance estimates (e.g., 95%
    CIs) or reframe the results as descriptive statistics without implying statistical
    superiority/difference.'
- id: 597b3ea5706a
  severity: science
  text: The clustering method (K-medoids) uses a weighted Levenshtein distance with
    fixed substitution costs (0.33, 0.66, 1.0). The sensitivity of the resulting medoids
    and subsequent task coverage to these specific weight choices is not analyzed.
    A brief ablation or justification for these weights would strengthen the statistical
    validity of the diversity claims.
artifact_hash: 004a982517336ff5bb70731546f888ea558d17b145625434a810ca9028fcd39c
artifact_path: projects/PROJ-653-https-arxiv-org-abs-2605-28556/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T08:54:35.534601Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The paper presents a novel pipeline (TASTE) for generating agent benchmarks, but the statistical rigor of the evaluation results requires strengthening before the claims of "severe drops" and "improved coverage" can be fully substantiated.

**Lack of Variance Estimates and Significance Testing**
The primary statistical concern lies in Section 5 (Results) and Table 1. The authors report single-point accuracy scores (e.g., 0.34 vs 0.72) and calculate relative percentage changes. However, LLM performance is inherently stochastic; a single run per task does not capture the variance of the model's behavior. The NeurIPS Checklist (Item 7) explicitly admits that "Table 1 reports point estimates... without error bars due to API-cost constraints." While cost is a practical constraint, it does not negate the need for statistical rigor when making comparative claims. Without confidence intervals (CIs) or standard errors, it is impossible to determine if the observed performance drops are statistically significant or merely artifacts of random variation in the specific task samples or model seeds. The authors should either:
1.  Perform a bootstrap analysis over the task set to generate 95% confidence intervals for the mean accuracy.
2.  Run a subset of tasks with multiple seeds to estimate variance.
3.  Explicitly reframe the results as "observed descriptive statistics" rather than definitive evidence of performance degradation, acknowledging the lack of statistical significance testing.

**Clustering Parameter Sensitivity**
In Section 4.2, the authors employ K-medoids clustering with a weighted Levenshtein distance. The substitution costs (0.33 for same-group, 0.66 for same-type, 1.0 otherwise) are fixed hyperparameters. The statistical validity of the resulting "diverse" clusters depends heavily on these weights. There is no sensitivity analysis provided to show how robust the medoid selection and subsequent coverage metrics are to variations in these weights. A small ablation study or a theoretical justification for these specific values would improve the reproducibility and statistical soundness of the diversity claims.

**Coverage Metrics Aggregation**
The coverage improvements (e.g., "+124% WED") are reported as aggregate percentages. It is unclear if these are mean values across the dataset or values derived from the full set. Given the small sample sizes per domain (50-114 tasks), the distribution of these metrics (e.g., skewness in sequence lengths) should be reported to ensure the mean is a representative statistic.

In summary, while the methodology is sound, the statistical presentation of the results is currently insufficient to support the strong claims of benchmark saturation and difficulty. Addressing the lack of variance estimates is critical.
