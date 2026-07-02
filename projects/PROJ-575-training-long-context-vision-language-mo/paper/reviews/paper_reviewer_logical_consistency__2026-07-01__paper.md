---
action_items:
- id: 9862536efdf0
  severity: writing
  text: The paper's logical flow regarding the derivation of the final training recipe
    contains several inconsistencies between the presented data and the stated conclusions.
    First, the claim of generalization to 256K and 512K contexts "without additional
    training or adaptation" (Abstract, Section 1, Section 6) is logically fragile.
    Section 3 and Appendix A explicitly state that the mRoPE base frequency was scaled
    from $1\times10^6$ to $4\times10^6$ to extend the context from 32K to 128K. Standard
    trans
artifact_hash: 27eba2e5ea40297ff1b355e2383ef9ee011ad854079e699d6346f41869d2df3c
artifact_path: projects/PROJ-575-training-long-context-vision-language-mo/paper/specs/001-paper/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:39:12.964852Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper's logical flow regarding the derivation of the final training recipe contains several inconsistencies between the presented data and the stated conclusions.

First, the claim of generalization to 256K and 512K contexts "without additional training or adaptation" (Abstract, Section 1, Section 6) is logically fragile. Section 3 and Appendix A explicitly state that the mRoPE base frequency was scaled from $1\times10^6$ to $4\times10^6$ to extend the context from 32K to 128K. Standard transformer architectures with fixed positional embeddings (even with scaled bases) typically degrade significantly when extrapolating 4x beyond the training window (128K to 512K) without further adaptation or specific extrapolation techniques (e.g., NTK-aware scaling at inference). The paper asserts this generalization happens "without adaptation," yet the training setup itself involved a significant adaptation (frequency scaling). The logical gap lies in whether the 4e6 base was empirically proven to support 512K, or if the claim conflates the training adaptation with the inference claim.

Second, there is a clear citation error in Section 5.2 ("Multi-Task Long-Context Data Mixture"). The text states: "The best performance in the extraction-to-reasoning ratio grid search was obtained with a ratio of 8:2 [UNRESOLVED-CLAIM: c_d514205c] in \cref{tab:vqa_effectiveness}." This is logically invalid because Table 1 (`tab:vqa_effectiveness`) compares VQA tasks against OCR tasks, not the extraction-to-reasoning ratios. The correct evidence is in Table 2 (`tab:extract_reason_ratio`). This disconnect breaks the logical chain between the claim and the supporting data.

Third, the conclusion to adopt "pure long-context training" (0% short data) in Section 5.3 is not fully supported by the trade-off analysis. Table 3 shows that while 0% short data yields the highest long-context score (57.70), it results in a drop in short-context performance (65.48 vs. 66.47 baseline). The text acknowledges that a 20% mix yields the best short-context score (66.53) and a 40% mix offers a "better practical balance." However, the authors discard these findings to choose the 0% mix solely to "maximize long-context capability." While a valid engineering choice, the logical leap to claim this is the definitive "recipe" without addressing the degradation in short-context capabilities contradicts the earlier finding that instruction-formatted long data *should* preserve short capabilities (which it only partially did). The logic would be stronger if the authors explicitly justified why the marginal gain in long-context performance outweighs the loss in short-context robustness, rather than presenting it as the natural outcome of the "preservation" hypothesis.
