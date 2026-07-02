---
action_items:
- id: a8b2cd165e84
  severity: science
  text: The manuscript defines edge weights (Table 1) and node importance scores (Eq.
    6-7) using fixed hyperparameters (e.g., gamma=0.5, beta_cite=1.00) without reporting
    any sensitivity analysis, ablation studies, or statistical justification for these
    specific values. The impact of these choices on retrieval performance is unquantified.
- id: b2027342bfb9
  severity: science
  text: The paper claims a 'neuro-symbolic retrieval algorithm' but provides no statistical
    evaluation metrics (e.g., Precision@K, Recall@K, NDCG, or Mean Average Precision)
    comparing the proposed method against baselines. Without quantitative results
    and confidence intervals, the claim of 'seamless transition' and 'reduced inference
    cost' is unsupported by evidence.
- id: 2972883f8063
  severity: science
  text: The construction pipeline relies on LLMs (Qwen3) for keyword extraction and
    scoring. The manuscript fails to report inter-annotator agreement (e.g., Cohen's
    Kappa) or validation statistics against a human-annotated gold standard to assess
    the reliability and bias of these extracted features.
artifact_hash: f3ce028cf68a2eb124d9418ea236e7f52f710c30a6edb26c69bffcf6c534c941
artifact_path: projects/PROJ-623-sciatlas-a-large-scale-knowledge-graph-f/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T07:06:31.446260Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents a large-scale knowledge graph (SciAtlas) and a neuro-symbolic retrieval pipeline. However, from a statistical analysis perspective, the paper lacks the necessary quantitative rigor to support its claims of efficacy and novelty.

First, the retrieval algorithm relies heavily on a set of fixed hyperparameters (e.g., $\gamma=0.5$ in Eq. 7, $\beta_{cite}=1.00$ in Table 1, $\lambda$ weights in Eq. 10). The manuscript provides no statistical justification for these specific values. There is no sensitivity analysis, ablation study, or cross-validation reported to demonstrate that these parameters are optimal or robust. Without this, the system's performance appears arbitrary rather than empirically derived.

Second, and most critically, the paper makes strong claims about the effectiveness of the retrieval method ("seamless transition," "reducing inference cost") but presents **no statistical evaluation results**. There are no tables or figures reporting standard information retrieval metrics such as Precision@K, Recall@K, NDCG, or Mean Average Precision (MAP) on a held-out test set. Furthermore, there is no comparison against baseline methods (e.g., pure vector search or keyword search) with statistical significance testing (e.g., paired t-tests or Wilcoxon signed-rank tests) to validate that the proposed method outperforms existing approaches. The absence of confidence intervals or error bars on any reported metrics (if they were present in the unseen figures) would also be a concern, but the total lack of quantitative performance data is the primary deficit.

Finally, the construction of the graph relies on an LLM (Qwen3) to extract keywords and assign importance scores. The reliability of these features is crucial for the downstream graph traversal. The manuscript does not report any validation statistics, such as inter-annotator agreement (Cohen's Kappa) or correlation with human-annotated ground truth, to assess the quality and consistency of the LLM-generated features. Without this validation, the statistical soundness of the graph's semantic layer is questionable.

To be accepted, the authors must provide a rigorous statistical evaluation of their retrieval system, including baseline comparisons, significance testing, and sensitivity analysis of the hyperparameters.
