---
action_items:
- id: 0e069bfb714e
  severity: science
  text: Verify the claim that 'SSMs with linear updates are no more expressive than
    an ordinary transformer' (Section 5) against the cited source Merrill2025illusion.
    Ensure the citation does not overstate the equivalence, as some linear SSMs may
    have distinct inductive biases or efficiency profiles not captured by pure expressivity
    bounds.
- id: a6a5c9c89ce5
  severity: science
  text: Confirm that the citation 'baldelli2026' (Section 2, footnote) actually contains
    the formal proof regarding 'failure of standard models to reliably maintain a
    consistent hidden state' as attributed. The bibliography lists this as a 2026
    preprint; verify the specific claim exists in the referenced text.
- id: 832ce621970b
  severity: science
  text: Check the attribution of the 'bank' ambiguity example to 'lepori2025' (Section
    2). Ensure the paper explicitly demonstrates the 'racing thoughts' mechanism (disambiguation
    at layer 6 vs. shallow layers) for this specific example, rather than just reporting
    the error generally.
- id: e45c672f7ed6
  severity: science
  text: Validate the claim that 'depth recurrence... does not enable indefinite state
    tracking' (Section 3) against the cited 'merrill2025' or 'merrill2025illusion'.
    Ensure the distinction between 'depth recurrence' (looped) and 'step recurrence'
    is clearly supported by the cited theoretical bounds.
artifact_hash: 924b893a4650c3044c8ebca795788f41846a7a72e06ec4cbf52905fb73429333
artifact_path: projects/PROJ-746-the-topological-trouble-with-transformer/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T06:59:43.546948Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The manuscript makes several strong theoretical claims regarding the expressivity and state-tracking capabilities of various architectures, specifically contrasting feedforward transformers with recurrent and state-space models. While the overall argument is coherent, specific citations require verification to ensure they support the precise claims made.

In Section 2, the paper cites `baldelli2026` to formally address the failure of models to maintain consistent hidden states. Given that this is a 2026 preprint, it is critical to verify that the paper explicitly contains the formal proof or analysis attributed to it, rather than just anecdotal evidence. Similarly, the claim that "SSMs with linear updates are no more expressive than an ordinary transformer" (Section 5) relies heavily on `merrill2025illusion`. The review must confirm that this source indeed establishes a strict equivalence in expressivity that precludes linear SSMs from solving state-tracking problems that transformers cannot, or if the distinction is more nuanced (e.g., regarding efficiency or specific inductive biases).

Furthermore, the detailed mechanistic explanation of the "bank" ambiguity example (Section 2), specifically the claim that disambiguation occurs at the sixth block and is inaccessible to shallower layers, is attributed to `lepori2025`. The authors must ensure that `lepori2025` explicitly reports this specific layer-depth finding for this specific example, as opposed to a general observation of racing thoughts. If the cited paper only demonstrates the error without the specific layer-wise analysis, the claim is overstated.

Finally, the assertion in Section 3 that "depth recurrence... does not enable indefinite state tracking" is a central theoretical pillar. The citation `merrill2025` (or `merrill2025illusion`) must be checked to ensure it specifically addresses the limitations of *depth* recurrence (looped transformers) versus *step* recurrence, and that the proof holds for the specific definition of "indefinite tracking" used in the text. If the cited work only bounds the depth required for specific languages (like regular languages) without addressing the general state-tracking capacity of looped architectures, the claim may be too broad.
