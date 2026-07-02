---
action_items:
- id: 5e38c04803fd
  severity: science
  text: The paper claims a 'neuro-symbolic retrieval algorithm' achieves 'deterministic
    association discovery' but provides no quantitative evaluation (e.g., precision@k,
    recall, NDCG) against baselines. Without empirical metrics on a held-out test
    set, the efficacy of the proposed RWR and weighting scheme remains an unverified
    assertion.
- id: 28adb542102e
  severity: science
  text: The construction pipeline relies on a single LLM (Qwen3) for keyword extraction
    without reporting inter-annotator agreement, human validation, or error rates.
    The quality of the 3.76M keyword nodes is a critical dependency for the graph's
    utility, yet no evidence of extraction accuracy is provided.
- id: 464167f0384d
  severity: science
  text: The retrieval algorithm contains multiple tunable hyperparameters (e.g., theta_kw=0.7,
    lambda_emb=0.3, gamma=0.5). The manuscript does not describe the methodology used
    to select these values (e.g., grid search, ablation study) or report sensitivity
    analysis, raising concerns about overfitting to anecdotal examples.
artifact_hash: f3ce028cf68a2eb124d9418ea236e7f52f710c30a6edb26c69bffcf6c534c941
artifact_path: projects/PROJ-623-sciatlas-a-large-scale-knowledge-graph-f/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T07:06:12.571146Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The manuscript presents SciAtlas, a large-scale knowledge graph, and a neuro-symbolic retrieval pipeline. While the scale of the data (43M papers, 3B edges) is impressive, the scientific evidence supporting the *efficacy* of the proposed retrieval method is currently insufficient.

The central claim is that the "neuro-symbolic retrieval algorithm" (combining keyword, semantic, and graph-based RWR) outperforms or meaningfully improves upon existing vector/keyword matching. However, Section 4 (Neuro-Symbolic Retrieval) and Section 5 (Downstream Applications) describe the *mechanism* and provide qualitative examples (e.g., "An Example of Idea Grounding") but lack any quantitative evaluation. There are no reported metrics such as Precision@K, Recall, Mean Average Precision (MAP), or NDCG on a standard benchmark or a held-out test set. Without these metrics, it is impossible to verify if the complex weighting scheme (Eqs. 1-10) actually yields better results than a simple vector search baseline. The claim of "deterministic association discovery" is a qualitative assertion, not a scientifically validated result.

Furthermore, the construction of the graph relies heavily on an LLM (Qwen3) for keyword extraction (Section 3.2). The quality of these 3.76M keyword nodes is fundamental to the graph's topology. The paper provides no evidence of the extraction quality, such as human evaluation scores, inter-annotator agreement, or comparison against a gold-standard keyword set. If the keyword extraction is noisy, the "semantic level" and "conceptual level" of the graph may be compromised, invalidating the downstream retrieval performance.

Finally, the retrieval algorithm introduces numerous hyperparameters (e.g., $\theta_{kw}=0.7$, $\lambda_{emb}=0.3$, $\gamma=0.5$, $\alpha$ in RWR). The manuscript does not describe how these were tuned. There is no mention of an ablation study to determine the contribution of each component (e.g., does the RWR actually add value over the seed matching?). The lack of sensitivity analysis or parameter justification suggests the results may be fragile or overfit to the specific examples shown. To support the scientific claims, the authors must provide quantitative benchmarks, validation of the data construction pipeline, and an analysis of the algorithm's hyperparameters.
