---
action_items:
- id: 52ff02d62569
  severity: science
  text: The paper reports results from a single deterministic run (temperature 0.0)
    without any measure of variance (e.g., standard deviation, confidence intervals)
    or statistical significance testing. Given the small performance gaps between
    OmniRetrieval and KB Routing in some backbones (e.g., +3.86 pp on GPT-5.4 for
    Source Selection), the authors must provide evidence that these improvements are
    not due to random variation or specific dataset idiosyncrasies.
- id: a3b256049cd1
  severity: science
  text: The evaluation relies heavily on an 'LLM-as-a-Judge' metric (GPT-5.4-mini)
    for semantic equivalence without reporting inter-rater reliability or calibration
    against human annotations. The statistical validity of using a single LLM instance
    as the ground truth for 'correctness' across 13 datasets is unverified and requires
    a sensitivity analysis or comparison with human-annotated subsets.
- id: 6cd06b2e5c54
  severity: science
  text: The macro-averaging of metrics across four heterogeneous paradigms (Search,
    SQL, SPARQL, Cypher) with vastly different baseline difficulties and sample sizes
    (e.g., 286 SQL DBs vs 15 Cypher graphs) may obscure significant performance disparities.
    The authors should clarify if the reported averages are weighted by dataset size
    or if a stratified analysis was performed to ensure the results are not dominated
    by the largest paradigm.
artifact_hash: 6b55048d0f0cf12263aa0420c5a331e1157aabe9768489e7c4eadd1c3653e932
artifact_path: projects/PROJ-644-omniretrieval-unified-retrieval-across-h/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T16:48:40.908085Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in the manuscript lacks necessary rigor to fully support the claimed superiority of OmniRetrieval over baselines. The primary issue is the absence of variance estimation. As stated in the Implementation Details (Section 5.4), all experiments were run with a sampling temperature of 0.0, resulting in deterministic outputs. Consequently, the reported metrics in Table 1 and Table 2 are single-point estimates without standard deviations, confidence intervals, or error bars. In the absence of multiple random seeds or bootstrap resampling, it is impossible to determine if the observed improvements (e.g., the 3.86 percentage point gain in Source Selection Accuracy on GPT-5.4 over KB Routing) are statistically significant or merely artifacts of the specific test set composition.

Furthermore, the reliance on an LLM-as-a-Judge (GPT-5.4-mini) as a primary evaluation metric introduces a potential source of systematic bias that is not statistically characterized. The paper does not report inter-rater reliability (e.g., Cohen's kappa) if multiple judges were used, nor does it provide a calibration study against human-annotated ground truth to validate the judge's accuracy. Without this, the "LLM-as-a-Judge" scores should be treated as heuristic proxies rather than definitive statistical evidence of semantic equivalence.

Finally, the macro-averaging strategy across the four retrieval paradigms (Search, SQL, SPARQL, Cypher) warrants scrutiny. The datasets are highly imbalanced in terms of knowledge base counts (286 SQL DBs vs. 15 Cypher graphs) and inherent difficulty. A simple macro-average may not accurately reflect the model's performance across the entire heterogeneous landscape if one paradigm dominates the aggregate score. The authors should clarify whether the averaging is weighted by the number of samples or if a stratified analysis was conducted to ensure the results are robust across all sub-domains. To meet statistical standards for publication, the authors should re-run experiments with multiple seeds to report variance or perform a significance test (e.g., paired t-test or Wilcoxon signed-rank test) on the results.
