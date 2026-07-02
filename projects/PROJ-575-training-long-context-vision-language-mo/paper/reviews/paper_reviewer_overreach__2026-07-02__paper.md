---
action_items:
- id: e6ec171552c7
  severity: science
  text: Claims of generalization to video/web tasks (Abstract) are unsupported; training
    is PDF-only. Improvements on MM-NIAH/Video-MME do not prove true modality transfer
    beyond static document retrieval skills.
- id: e996348a210f
  severity: science
  text: The claim of 512K generalization (Abstract) is overreaching. Evaluation uses
    random negative document padding (App A.4.2), testing distractor robustness, not
    genuine 512K multimodal sequence processing.
- id: 424838c27dc8
  severity: writing
  text: The conclusion that short-context data is unnecessary (Sec 5.3) overstates
    a minor performance drop. The claim of recipe transfer to stronger backbones relies
    on a single, already long-context trained model (Qwen3-VL).
artifact_hash: 27eba2e5ea40297ff1b355e2383ef9ee011ad854079e699d6346f41869d2df3c
artifact_path: projects/PROJ-575-training-long-context-vision-language-mo/paper/specs/001-paper/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:44:11.827978Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: full_revision
---

The paper significantly overreaches in its claims regarding the generalization capabilities of the proposed MMProLong model. The primary issue lies in extrapolating results from a specific training domain (PDF documents) to entirely different modalities and contexts without sufficient evidence.

First, the claim that the model generalizes to "webpage-based multimodal needle retrieval" and "long-video understanding" (Abstract, Introduction) is not supported by the training data. The model is trained exclusively on PDF documents. While the evaluation benchmarks (MM-NIAH, Video-MME) show score improvements, the paper does not provide evidence that the model has learned the specific visual reasoning required for dynamic web layouts or temporal video understanding. The improvement on these benchmarks could be attributed to general retrieval skills learned from PDFs rather than true modality transfer. The leap from "PDF VQA" to "video understanding" is a significant over-extrapolation.

Second, the claim of generalization to 256K and 512K contexts (Abstract, Section 6.2) is misleading. The evaluation at these lengths involves padding the input with "randomly sampled negative documents" (Appendix A.4.2). This tests the model's ability to ignore irrelevant text in a static, document-like format, not its ability to process a coherent 512K multimodal sequence. The paper conflates "distractor robustness" with "long-context capability," leading to an unjustified claim of generalization to extreme context lengths.

Finally, the recommendation to use "pure long-context training" without short-context data (Section 5.3) overstates the findings. While the performance drop is small, the paper presents this as a definitive rule ("largely preserves") rather than a trade-off. Additionally, the claim that the recipe works for "stronger long-context backbones" is based on a single experiment with Qwen3-VL-8B, a model that already possesses native long-context capabilities, making the "extension" claim weak and the generalization to other architectures unproven. The paper needs to temper these claims to reflect the actual scope of the experiments.
