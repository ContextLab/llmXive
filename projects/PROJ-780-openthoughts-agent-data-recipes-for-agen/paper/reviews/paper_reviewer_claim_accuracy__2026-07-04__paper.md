---
action_items:
- id: 15d64b4071bd
  severity: writing
  text: The paper presents a rigorous ablation study on data curation for agentic
    models, with most numerical claims aligning well with the provided tables. However,
    there are specific instances where the textual claims rely on unsupported or potentially
    hallucinated external facts, and one instance of ambiguous comparative logic.
    First, the Introduction and Section 3.5 repeatedly reference "GPT-5.3-Codex" as
    a benchmark model and a teacher model. As of the current date, GPT-5 has not been
    publicly rele
artifact_hash: 1762f575d6ad502232c74311f4c0e12a6d2ed21a38bf5e7d1493821d45367039
artifact_path: projects/PROJ-780-openthoughts-agent-data-recipes-for-agen/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-04T02:23:47.429111Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper presents a rigorous ablation study on data curation for agentic models, with most numerical claims aligning well with the provided tables. However, there are specific instances where the textual claims rely on unsupported or potentially hallucinated external facts, and one instance of ambiguous comparative logic.

First, the Introduction and Section 3.5 repeatedly reference "GPT-5.3-Codex" as a benchmark model and a teacher model. As of the current date, GPT-5 has not been publicly released, and no specific "5.3" version exists in the public record or the provided bibliography. The claim that it is the "best-performing model" is therefore unsupported by any cited evidence and appears to be a hallucination or a placeholder that was not updated. This undermines the credibility of the teacher model ablation results which hinge on this comparison.

Second, the claim in Section 3.5 that "GLM-4.7-AWQ is the best teacher" is ambiguous and potentially misleading when cross-referenced with Table 5. While GLM-4.7 achieves the highest *average* normalized score in that specific table (18.16), Kimi K2.5 achieves a higher raw average (18.59) and a significantly higher SWE-Bench score (33.33% vs 28.00%). The text justifies the claim by noting a ~5% decrease on Terminal-Bench 2.0 when using GPT-5.3, but it fails to acknowledge that Kimi K2.5 outperforms GLM-4.7 on the primary SWE-Bench metric. The "best teacher" label should be qualified (e.g., "best balanced teacher" or "best on average") or the table should be re-evaluated to ensure the conclusion matches the data.

Finally, while the 30 pp and 10 pp impact claims in Section 3.1 are numerically supported by the range in Table 3, the 10 pp figure on Terminal-Bench is driven largely by the 0.37% outlier (AgentTuning-OS). It would be more accurate to specify that the range spans from the top strategy to the bottom outlier, rather than implying a typical variance of 10 pp across all strategies.

These issues are primarily matters of precision and verification rather than fundamental scientific flaws, but they require correction to ensure the claims are strictly supported by the evidence presented.
