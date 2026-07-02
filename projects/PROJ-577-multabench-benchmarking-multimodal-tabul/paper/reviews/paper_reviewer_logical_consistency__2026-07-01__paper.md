---
action_items:
- id: 9ad28b5552be
  severity: writing
  text: The paper presents a coherent argument for the necessity of Target-Aware Representations
    (TAR) in Multimodal Tabular Learning (MMTL), supported by a rigorous curation
    pipeline. However, there are minor logical inconsistencies between the stated
    definitions and the formal criteria, as well as slight overgeneralizations in
    the causal claims regarding model capacity. First, there is a discrepancy in the
    definition of "Joint Signal." In Section 3.1, the text states that joint performance
    must exceed
artifact_hash: 28e097e31933ecce294eb34fd92a9e53c4dcbbab117fcc0a77af75a314777084
artifact_path: projects/PROJ-577-multabench-benchmarking-multimodal-tabul/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:48:02.313303Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper presents a coherent argument for the necessity of Target-Aware Representations (TAR) in Multimodal Tabular Learning (MMTL), supported by a rigorous curation pipeline. However, there are minor logical inconsistencies between the stated definitions and the formal criteria, as well as slight overgeneralizations in the causal claims regarding model capacity.

First, there is a discrepancy in the definition of "Joint Signal." In Section 3.1, the text states that joint performance must exceed the "union of unimodal performances." In contrast, the formal acceptance criteria in Appendix A.3.3 define the gain as exceeding the "strongest unimodal baseline" (i.e., the maximum of the two unimodal scores). Logically, exceeding the union (sum or set union) is a much stricter condition than exceeding the maximum. If the curation pipeline used the "max" definition (as the formula suggests), the textual claim of "union" is inaccurate and creates a logical gap between the motivation and the execution. The text in Section 3.1 should be revised to align with the formal definition in the appendix.

Second, the causal mechanism for the failure of frozen embeddings is slightly imprecise. The paper argues that frozen embeddings lose "fine-grained details" (Section 1) and that this necessitates TAR. The experimental validation involves finetuning only the *last 3 layers* of the encoder (Section 3.2, Appendix A.1). While this supports the claim that the *final* representation is task-agnostic, it does not logically prove that the *entire* embedding process is insufficient. The lower layers might already contain the necessary signal, but the final projection layer fails to extract it. The conclusion should be refined to state that the *final projection* or *top layers* of frozen encoders are the bottleneck, rather than implying the entire pre-trained representation is fundamentally flawed.

Finally, the claim in Section 5 that "increased representational capacity does not guarantee that target-relevant signals are retained" based on the "TAR Small > Frozen Large" result is a strong causal inference. While the result is valid, the conclusion could be interpreted as a failure of capacity itself, whereas the more precise logical conclusion is that *frozen* large models fail to adapt to specific tasks, whereas *finetuned* small models succeed. The distinction between "capacity" and "adaptability" is crucial here. The text should clarify that the failure lies in the *frozen* nature of the large model, not necessarily in the capacity of large models in general.

Addressing these points will tighten the logical consistency between the paper's premises, its experimental design, and its conclusions.
