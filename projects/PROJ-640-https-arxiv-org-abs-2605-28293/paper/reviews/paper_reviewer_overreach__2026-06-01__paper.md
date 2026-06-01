---
action_items:
- id: 1f3942bd585f
  severity: writing
  text: Correct the numerical claims in Appendix Section 'Performance Superiority
    Across Diverse Metrics' which cite Steam IoR as 1300-1500 and CTR/Coherence as
    0.89/0.95, contradicting Table 1 (Steam IoR 340.18; MovieLens CTR 0.8543/Coherence
    0.8422). This constitutes an unsupported over-claim of performance.
- id: 7d76af866cb5
  severity: science
  text: Qualify the theoretical claims regarding Theorem 1. The proof assumes a simplified
    homogeneous stopping model, but the implementation uses semantic IDs and complex
    reward structures. Explicitly state that the theorem provides intuition rather
    than a rigorous guarantee for the full system to avoid overgeneralization.
artifact_hash: 04be55bc6e5d8d960cc49a3798cf6dcfe7112c356a8019a56a3a1b07b8b8ef6d
artifact_path: projects/PROJ-640-https-arxiv-org-abs-2605-28293/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-01T21:51:34.590088Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper presents a compelling RL framework for proactive recommendation, with empirical results in Tables 1-4 generally supporting the claims of superiority over baselines. However, there are significant instances of over-claiming in the narrative text and theoretical framing that exceed the provided evidence.

First, the Appendix section "Performance Superiority Across Diverse Metrics" explicitly claims MovieLens-1M CTR of ~0.89 and Coherence of 0.95, and Steam IoR between 1300-1500. These numbers contradict Table 1, which reports MovieLens CTR 0.8543, Coherence 0.8422, and Steam IoR 340.18. Claiming performance metrics that are not supported by the main experimental tables is a direct over-claim. These discrepancies must be corrected to align with the empirical data.

Second, the theoretical analysis relies on Theorem 1, which is proven for a simplified model where the policy makes only `continue`/`stop` decisions with a fixed stopping probability. The authors claim this analysis "remains valid" for the semantic ID implementation (Appendix A.1). While the intuition holds, the complexity of token-level generation and multi-objective rewards introduces variables not covered by the proof. Stating the theorem remains valid without qualification overstates the theoretical guarantee. The claim should be tempered to reflect that the theorem motivates the design rather than rigorously proving the full system's behavior.

Finally, the claim of "generalizable principles" based on cross-evaluator analysis (Tables 2-4) is slightly overreaching. The evaluators (SASRec, GRU4Rec, BERT4Rec, LightSANs) are all standard sequential recommenders trained on the same domain data. True generalization to different recommendation paradigms or domains is not demonstrated. Addressing these discrepancies is necessary to ensure the paper's claims accurately reflect the data.
