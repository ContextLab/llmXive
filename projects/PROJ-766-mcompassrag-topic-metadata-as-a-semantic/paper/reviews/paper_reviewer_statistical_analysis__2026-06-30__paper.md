---
action_items:
- id: 68bd505c1322
  severity: writing
  text: 'The statistical analysis in the paper requires clarification and additional
    rigor to fully support the performance claims. First, the definition of the primary
    retrieval metric, Information Efficiency (IE), is defined in Section 5.1 as the
    product of Precision and Recall ($\mathrm{IE} = P \times R$). This is a non-standard
    metric in information retrieval literature, where the F1-score (harmonic mean)
    or nDCG are typically used. The product metric has distinct statistical properties:
    it heavily p'
artifact_hash: 5e7163c1713464843d620f2c37705ca96ededa7c235cfa3e5a0986f0a19b0aa7
artifact_path: projects/PROJ-766-mcompassrag-topic-metadata-as-a-semantic/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T15:13:16.115868Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in the paper requires clarification and additional rigor to fully support the performance claims.

First, the definition of the primary retrieval metric, Information Efficiency (IE), is defined in Section 5.1 as the product of Precision and Recall ($\mathrm{IE} = P \times R$). This is a non-standard metric in information retrieval literature, where the F1-score (harmonic mean) or nDCG are typically used. The product metric has distinct statistical properties: it heavily penalizes cases where either precision or recall is low, potentially exaggerating the "efficiency" gap between methods that have high precision but moderate recall. For instance, a method with P=0.9 and R=0.5 yields IE=0.45, while F1=0.64. The authors must justify why this specific metric was chosen over standard alternatives or provide a supplementary analysis using F1@k and nDCG@k to demonstrate that the reported 8.24% average improvement is robust to the choice of metric.

Second, while Table 1 reports standard deviations across three runs, it does not indicate whether the differences between MCompassRAG and the baselines are statistically significant. With only $n=3$ runs, the power of statistical tests is limited, but reporting p-values from a paired t-test or Wilcoxon signed-rank test is essential. For example, on the DRBench dataset, the IE gap between MCompassRAG (47.97) and SAKI-RAG (37.47) is substantial, but without a significance test, it is unclear if this difference is consistent or driven by variance in specific queries. The authors should explicitly state the statistical significance of their improvements over the strongest baselines.

Third, the latency claims in the abstract ("5x lower latency") and Section 5.2 rely on mean values. Latency distributions in retrieval systems are often right-skewed due to occasional network or computation spikes. Reporting only the mean can be misleading. The authors should provide the median latency and the interquartile range (IQR) for both MCompassRAG and the baselines. Additionally, a confidence interval for the latency reduction ratio would strengthen the claim of efficiency.

Finally, the ablation studies in Table 3 and Figure 3 show performance drops when components are removed, but the statistical significance of these drops is not quantified. Given the small effect sizes in some ablations (e.g., the drop in IE on Dragonball when removing the selection policy is ~0.44 points), it is crucial to verify if these differences are statistically distinguishable from noise.

Addressing these points will ensure the statistical validity of the paper's conclusions.
