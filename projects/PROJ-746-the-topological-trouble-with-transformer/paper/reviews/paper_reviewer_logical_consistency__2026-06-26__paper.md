---
action_items:
- id: bc9c5776e472
  severity: science
  text: Resolve the apparent contradiction between the Abstract (dynamic depth bypasses
    limit) and Section 3 (depth recurrence does not enable indefinite tracking). Explicitly
    define 'dynamic depth' vs 'depth recurrence' to ensure logical consistency.
- id: 5bd0d7e0ba02
  severity: science
  text: Clarify the causal mechanism for the 'state shifting upward' claim in Section
    3. Distinguish between unrolled graph depth and physical layer depth to support
    the argument that parallelization, not just depth, limits state tracking.
artifact_hash: 924b893a4650c3044c8ebca795788f41846a7a72e06ec4cbf52905fb73429333
artifact_path: projects/PROJ-746-the-topological-trouble-with-transformer/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-26T10:24:12.986734Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper presents a coherent theoretical argument regarding the limitations of feedforward transformers in state tracking. The core premise—that state representations must deepen with each step in a feedforward architecture—is logically sound and well-supported by Figure 1 and the discussion of the "bank" example (Section 2). However, there are logical inconsistencies regarding the classification and capabilities of recurrent architectures that require clarification.

First, there is a contradiction between the Abstract and Section 3. The Abstract states that the depth limit "can be bypassed by dynamic depth models" (Abstract, lines 12-13). However, Section 3 claims that "Depth recurrence... does not enable indefinite state tracking" (Section 3, paragraph 5). Since dynamic depth models (e.g., Adaptive Computation Time) are a form of depth recurrence, these statements conflict. The paper must explicitly distinguish between fixed-depth recurrence (looped transformers) and adaptive-depth recurrence to resolve this logical gap.

Second, the causal claim that "the state representation still shifts upward due to the parallel propagation of activation across steps $t$" (Section 3, paragraph 5) is not fully supported for all depth-recurrent architectures. In models like the Universal Transformer, layers are reused across tokens, meaning the state $s_t$ does not necessarily occupy a deeper physical layer than $s_{t-1}$ in the unrolled graph. The limitation arises from parallel token processing, not necessarily depth shifting. The argument would be logically tighter if it attributed the limitation to the inability to parallelize across the sequence length (as noted in the footnote defining recurrence steps) rather than the geometric "shifting" of state.

Finally, the taxonomy in Table 1 lists "looped transformer" under "Depth" recurrence but leaves the "Ratio = 1" and "Ratio < 1" cells empty for Depth. The text notes "We have not succeeded in identifying any examples of work that lies in the empty cells" (Section 3, paragraph 8). This is an empirical claim about the literature, not a logical deduction, but it weakens the completeness of the taxonomy if the definitions allow for such architectures. Clarifying why these cells are empty based on architectural constraints would strengthen the logical consistency of the proposed framework.

These issues do not invalidate the paper's central thesis but require precise definitions to ensure the conclusions follow rigorously from the premises.
