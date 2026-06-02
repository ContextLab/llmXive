---
action_items:
- id: 7bc421291007
  severity: science
  text: 'Quantitative retrieval benchmarks missing: No Recall@K, MRR, or NDCG scores
    provided against baselines (e.g., BM25, dense retrieval) to validate topological
    reasoning claims.'
- id: 87eda2b0fdca
  severity: science
  text: 'Cost reduction claim unsupported: The claim of ''significantly reducing reasoning
    costs'' lacks empirical latency or token-count comparison data against LLM-based
    deep research frameworks.'
- id: 274c478044b8
  severity: science
  text: 'Ablation study needed: Hyperparameters (lambda values, restart probability
    alpha) are set to defaults without sensitivity analysis to prove robustness.'
artifact_hash: 2d03fe1e69a43f0e46e7519d0318b0a18b1fbc7fdac764f3d055c5b8406f650f
artifact_path: projects/PROJ-623-sciatlas-a-large-scale-knowledge-graph-f/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-02T00:50:38.433892Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: full_revision
---

The paper makes strong empirical claims regarding the efficacy of the SciAtlas knowledge graph and its retrieval algorithm, yet the scientific evidence supporting these claims is currently insufficient. In the Abstract and Introduction, the authors claim the system achieves a "transition from simple semantic matching to deterministic association discovery" and "significantly reducing reasoning costs." However, Section 3 (`sections/retrieval.tex`) details the neuro-symbolic algorithm without presenting any quantitative evaluation results. There are no reported metrics such as Recall@K, Mean Reciprocal Rank (MRR), or Normalized Discounted Cumulative Gain (NDCG) compared against standard baselines (e.g., BM25, pure dense retrieval). Without these metrics, the assertion that the graph topology provides superior "topological reasoning" remains an unverified hypothesis.

Furthermore, the cost reduction claim is unsupported by data. The paper states the retrieval process completes "within 2 minutes, significantly shorter than LLM-based deep research frameworks" (Section 3), but provides no latency measurements or token consumption logs to substantiate this comparison. A controlled experiment measuring end-to-end time and computational cost against the cited agentic frameworks is required. Additionally, the application examples in Section 4 (`sections/application.tex`) are purely qualitative. The authors explicitly acknowledge in Section 5 (`sections/future.tex`) that they "merely present running examples... remaining at the qualitative analysis level." While system descriptions are valuable, the central claim that SciAtlas can "empower the full loop of automated scientific research" requires empirical validation of downstream task performance (e.g., idea novelty scores, trend prediction accuracy). Finally, the scoring fusion weights (Eq. 10) and random walk parameters (alpha, epsilon) are fixed defaults without ablation studies. Sensitivity analysis is needed to demonstrate that the performance gains are robust and not artifacts of specific hyperparameter tuning. To meet the standards of scientific evidence, the manuscript must include a benchmark dataset, report standard IR metrics with statistical significance, and provide a rigorous cost analysis.
