---
artifact_hash: 056c0815626cf07a81083eaa18cf8e32049f9408da58499094fbb2c8371aebce
artifact_path: projects/PROJ-570-leveraging-verifier-based-reinforcement/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-17T14:54:11.632647Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper presents a compelling framework, but several claims overreach the provided evidence or lack sufficient qualification.

First, the Abstract states there is a "clear scaling trend, with performance consistently improving from 3B to 7B parameters" (Line 45). However, Table `tab:full_rm_results` presents data for only two model sizes (3B and 7B). A scaling trend typically requires more data points to be statistically robust; claiming a "trend" based on two points is an overstatement of the evidence. This should be rephrased to "improvement with model size" rather than a "scaling trend."

Second, the Introduction claims to introduce the "first Chain-of-Thought (CoT) enabled reward model for image editing" (Line 115). Table 1 (Line 240) lists `Skywork-EditReward` as having "With thinks" checked. While the authors distinguish their "Verifier" approach via principle decomposition, the broad phrasing "first CoT enabled" risks conflating their specific method with general CoT reasoning present in concurrent work. This should be clarified to "first principle-based CoT verifier" to avoid ambiguity and potential conflict with existing literature.

Third, the evaluation methodology relies heavily on GPT-4.1 for semantic consistency and overall scores (Section 4.1). While the authors acknowledge in Section 4.3 that "scoring of image quality via the VLM isn't robust and reliable," the main results tables (`tab:model_evaluation`) still highlight "substantial gains" based on these metrics. This creates a tension where the primary evidence for downstream success relies on metrics the authors admit are weak. The human evaluation is relegated to the Appendix (Appendix `sec:human_eval`), which weakens the main claims of "substantial gains." The main text should either emphasize the human evaluation more or qualify the automated metric claims more strongly.

Finally, the claim that GCPO is a "novel reinforcement learning algorithm" (Abstract) is strong. While the formulation is specific, it appears to be a variant of existing contrastive RL methods (e.g., GRPO, DPO). The novelty should be tempered to reflect it as a specific adaptation for RRM training rather than a wholly new algorithm class, unless theoretical contributions are proven.

Recommendation: Minor revision to tone down scaling claims, clarify "first" claims against concurrent work, and balance the reliance on VLM metrics in the main text.
