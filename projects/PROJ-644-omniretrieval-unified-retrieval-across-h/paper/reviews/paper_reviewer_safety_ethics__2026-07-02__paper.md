---
action_items:
- id: 152681e0895d
  severity: writing
  text: The paper addresses a technically sound approach to heterogeneous retrieval
    but presents notable safety and ethical gaps regarding data privacy and content
    moderation. The primary concern lies in the Ethical Considerations (Section 7)
    and Use of Existing Artifacts (Appendix B.5). The authors explicitly state they
    "do not perform additional filtering for personally identifying information or
    offensive content" and defer entirely to upstream dataset policies. While the
    benchmark datasets (e.g., Sp
artifact_hash: 6b55048d0f0cf12263aa0420c5a331e1157aabe9768489e7c4eadd1c3653e932
artifact_path: projects/PROJ-644-omniretrieval-unified-retrieval-across-h/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T16:47:54.679200Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper addresses a technically sound approach to heterogeneous retrieval but presents notable safety and ethical gaps regarding data privacy and content moderation.

The primary concern lies in the **Ethical Considerations** (Section 7) and **Use of Existing Artifacts** (Appendix B.5). The authors explicitly state they "do not perform additional filtering for personally identifying information or offensive content" and defer entirely to upstream dataset policies. While the benchmark datasets (e.g., Spider, BEIR) are standard, the system's architecture—dispatching native queries to 309 distinct knowledge bases—amplifies the risk of retrieving and surfacing private or harmful content that might exist in real-world deployments or even in the "demo" graphs used (e.g., Neo4j movie graphs often contain real actor data). The current disclaimer is insufficient for a system designed to be a "general-purpose interface." The authors must clarify the specific nature of the 309 knowledge bases used: do any contain PII? If so, how was this mitigated? If not, the paper should explicitly warn that deploying this framework on uncurated, real-world databases without a PII filter is unsafe.

Furthermore, the **LLM-as-a-Judge** component (Section 4.3) relies on GPT-5.4-mini to evaluate semantic equivalence. The prompt for the judge (Figure 5 in Appendix) instructs the model to accept answers that are "faithfully implemented on a different KB" even if values differ. While methodologically sound for evaluation, this logic could inadvertently validate hallucinated or biased outputs if the judge model itself is biased or if the "alternative" KB contains harmful stereotypes. The paper should briefly discuss the safety alignment of the judge model used and whether any safety filters were applied to the judge's output or the candidate results before evaluation.

Finally, the **Source Selection** mechanism (Section 3.2) uses a long-context LLM to read the full catalog of source descriptors. If these descriptors or the underlying data contain sensitive metadata, the LLM could inadvertently leak this information in its selection rationale or generated queries. The authors should confirm that the structural context ($c_b$) provided to the LLM does not include sensitive schema details or data samples that could be exfiltrated via prompt injection or leakage.

In summary, while the technical contribution is significant, the safety review requires the authors to move beyond generic disclaimers and provide specific details on data sanitization, PII handling in the benchmark, and the safety alignment of the evaluation pipeline.
