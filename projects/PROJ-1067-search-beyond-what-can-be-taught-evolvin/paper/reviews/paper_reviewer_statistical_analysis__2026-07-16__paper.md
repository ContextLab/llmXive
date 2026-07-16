---
action_items:
- id: 8b6ccacfa787
  severity: writing
  text: "Tables 1 and 2 report single-point scores (e.g., 31.8) without uncertainty\
    \ metrics (SD/SE/CI). Given the stochastic nature of generation, this implies\
    \ false precision. Report mean \xB1 SD over \u22653 seeds for all results, or\
    \ explicitly state results are from a single run and soften claims of 'monotonic\
    \ improvement'."
- id: 4db87f34856a
  severity: science
  text: Section 5.1 claims 'monotonic improvement' and implies statistical significance
    without reporting p-values, confidence intervals, or hypothesis tests. With no
    variance reported, differences like 31.8 vs 31.2 are indistinguishable from noise.
    Perform paired tests with multiple-comparison correction or rephrase claims as
    observed trends.
artifact_hash: acdadb0a7d8b66991ef14c7c4247fe346cb02f508281ed63c55a7e05db3f0d02
artifact_path: projects/PROJ-1067-search-beyond-what-can-be-taught-evolvin/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-16T02:56:00.787291Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical treatment of the quantitative results in this paper is insufficient to support the strong inferential claims made regarding the efficacy of the co-training framework.

**1. Missing Uncertainty Reporting (Table 1 & Table 2)**
The primary results in Table 1 (Main Results) and Table 2 (Naive Search) are presented as single point estimates (e.g., "31.8", "76.5", "56.9") with no accompanying measure of variance (standard deviation, standard error, or confidence intervals). In the context of generative models, where results can vary significantly across different random seeds, training initializations, or even minor hyperparameter shifts, reporting a single number creates an illusion of precision that is not supported by the data. The paper mentions using "multiple seeds" for some baselines in passing, but the main comparison tables do not reflect this. Without error bars or variance metrics, a reader cannot judge whether the reported "monotonic improvement" (e.g., from 29.2 to 31.8) is a robust effect or a result of random fluctuation. This is a reporting failure that obscures the reliability of the findings.

**2. Unsubstantiated Claims of Significance**
The text frequently uses language implying statistical significance (e.g., "monotonic improvement," "exceeding frontier generators," "slightly exceeding the frontier oracle") without providing the statistical machinery to back it up. For instance, the claim that the proposed method "slightly exceeds" the oracle (31.8 vs 31.2) in Table 1 is presented as a definitive finding. However, without a hypothesis test (such as a paired t-test or a bootstrap test given the likely non-normal distribution of scores) and a reported p-value, this difference is indistinguishable from noise. The paper fails to address the multiple comparisons problem inherent in testing across three phases, two architectures, and multiple difficulty sets (Set I, II, III, NoSearch). If 24 comparisons are made at $\alpha=0.05$, one expects 1.2 false positives by chance alone. The absence of any correction (Bonferroni, Holm, or FDR) or explicit acknowledgment of this multiplicity undermines the validity of the "significant" gains claimed.

**3. Recommendation**
To rectify these issues, the authors must:
1.  Re-run the experiments (or aggregate existing runs if available) to report **mean ± standard deviation** over at least 3 independent seeds for every number in Tables 1 and 2.
2.  Perform appropriate **statistical hypothesis tests** (e.g., paired t-tests or Wilcoxon signed-rank tests) comparing the proposed method against the baselines for each stratum and architecture.
3.  Apply a **multiple-comparison correction** (e.g., Holm-Bonferroni) across the set of all reported comparisons and report the adjusted p-values.
4.  If re-running is not feasible, the text must be softened to describe "observed trends" rather than "statistically significant improvements," and the tables must explicitly state that results are from a single run.

Currently, the numbers in the paper do not mean what the text claims they mean: they are presented as definitive, significant improvements when they are merely point estimates with unknown variance.
