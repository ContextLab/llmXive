---
action_items:
- id: 2fcb2e5a87a6
  severity: science
  text: Section 3 claims depth recurrence fails because state 'shifts upward,' but
    re-using a layer implies state stays in place. Clarify why looped transformers
    cannot maintain state without depth exhaustion.
- id: 8874bd6a3aa3
  severity: science
  text: Section 4 states linear SSMs lack expressivity, then claims DeltaNet (linear)
    gains it with negative eigenvalues. Explicitly explain how negative eigenvalues
    bypass the cited theoretical bound.
- id: 8c03881eb7b9
  severity: science
  text: Section 2 uses the 'bank' failure to argue feedforward limits, yet admits
    compositional shortcuts exist. Explain why this specific task cannot be solved
    by such shortcuts to support the 'fundamental limit' claim.
artifact_hash: 924b893a4650c3044c8ebca795788f41846a7a72e06ec4cbf52905fb73429333
artifact_path: projects/PROJ-746-the-topological-trouble-with-transformer/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T06:59:25.042969Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The manuscript presents a coherent high-level argument that the feedforward topology of transformers creates a "depth bottleneck" for state tracking, necessitating recurrent mechanisms. However, several internal logical gaps weaken the causal claims regarding specific architectural classes.

First, in Section 3, the distinction between "depth recurrence" (looped transformers) and "feedforward depth" is muddled. The paper argues that depth recurrence fails to enable indefinite tracking because the state representation "shifts upward" (Section 3, paragraph 4). This contradicts the definition of recurrence provided earlier, where a layer is re-used. If a layer $L$ updates its own state $s_t = f(s_{t-1}, x_t)$, the state does not necessarily shift to a deeper layer $L+1$ in the unrolled graph; it remains in $L$. The claim that the state *must* shift upward appears to conflate depth recurrence with the standard feedforward propagation of a single pass. The argument requires a precise mechanistic explanation of why the state in a looped transformer cannot be maintained in a fixed layer without "running out of depth," or the claim must be qualified to exclude specific looped architectures that successfully maintain state.

Second, there is a logical tension in Section 4 regarding State-Space Models (SSMs). The text states that "SSMs with linear updates are no more expressive than an ordinary transformer," citing Merrill (2025). Immediately after, it claims DeltaNet (which relies on a linear delta rule) achieves "greater expressivity" when eigenvalues are negative. The paper fails to explicitly bridge this gap: does the negative eigenvalue extension technically violate the "linear update" constraint of the cited theorem, or is the initial claim about SSMs an overgeneralization? Without clarifying why the negative eigenvalue case escapes the expressivity bound, the argument that DeltaNet is superior appears to contradict the preceding theoretical claim.

Finally, the "bank" example in Section 2 is used to demonstrate a fundamental failure of feedforward models. However, the text acknowledges that for certain functions, the state updates can be composed into a single-step function $g$ (Section 2, paragraph 5). The paper does not logically explain why the "bank" disambiguation task *cannot* be solved by such a composition, thereby rendering the failure a limitation of the specific model's training rather than the architecture's topology. The conclusion that feedforward models "fundamentally limit" state tracking is too strong given the acknowledged existence of compositional shortcuts.
