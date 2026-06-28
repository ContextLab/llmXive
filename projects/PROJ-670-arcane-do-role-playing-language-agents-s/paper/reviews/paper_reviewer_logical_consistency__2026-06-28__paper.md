---
action_items: []
artifact_hash: 571d3401a83d0a75eab9bacc6292347c4c0034a87d0b29427ea4178c11f1a6c3
artifact_path: projects/PROJ-670-arcane-do-role-playing-language-agents-s/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-28T09:42:09.762866Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.5
verdict: accept
---

The paper presents a logically coherent argument for the necessity of evaluating character arcs in role-playing agents. The central premise—that static persona evaluation is insufficient for narrative immersion—is well-supported by the distinction between factual recall (TimeCHARA) and behavioral trajectory (ArcANE). The methodology logically follows: Character Arcs define the psychological trajectory, and Probes test alignment across phases.

The causal claim that Arc-grounded context outperforms retrieval-based methods (RAG) on Out-of-World scenarios is well-supported by the ablation in Section 5.1. The MixedArc ablation effectively rules out "structured-context bonus" by showing that swapping arc content degrades performance below Vanilla, confirming the specific psychological content drives the gain. Similarly, the POV control in Section 5.3 logically refutes the "register artifact" hypothesis for the fine-tuning gains, as forcing the register on the baseline did not close the performance gap.

The evaluation logic is sound. The use of an LLM judge is validated through human-anchored plausibility checks (Appendix A.6) and cross-judge replication (Appendix A.6), ensuring the metrics (APF, RPF, RAE, PTF) measure the intended construct. The distinction between In-Scenario, In-World, and Out-of-World probes is maintained consistently across experiments, and the results align with the theoretical expectation that retrieval fails on Out-of-World scenarios while Arc succeeds.

No internal contradictions were found. The claims regarding model performance (Table 1) follow directly from the reported data. The training data split (Section 3.3) is clearly defined to prevent leakage, and the results on low-popularity novels (Section 4.3) are logically consistent with the memorization control hypothesis. The paper's logical structure is robust.
