---
action_items:
- id: aae909817318
  severity: writing
  text: The paper is generally well-structured and the prose is clear, but several
    sections suffer from run-on sentences, wordiness, and minor structural disorganization
    that impede the reader's flow. In Section 3, the explanation of the hierarchical
    softmax (Answering RQ2) contains a dense, multi-clause sentence that obscures
    the causal link between the surrogate mass and the gradient flow. The reader must
    parse the sentence twice to understand that the parameterization of weights is
    what enables end-t
artifact_hash: c95e527feac1da55ce3c1a4f78a6e7762db38d741afaaaef5a9558e2491c1f16
artifact_path: projects/PROJ-1014-hierarchical-sparse-attention-done-right/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-09T02:52:25.971580Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_writing_quality
score: 0.0
verdict: minor_revision
---

The paper is generally well-structured and the prose is clear, but several sections suffer from run-on sentences, wordiness, and minor structural disorganization that impede the reader's flow.

In Section 3, the explanation of the hierarchical softmax (Answering RQ2) contains a dense, multi-clause sentence that obscures the causal link between the surrogate mass and the gradient flow. The reader must parse the sentence twice to understand that the parameterization of weights is what enables end-to-end learning. Splitting this into two distinct sentences would significantly improve readability.

The introduction to the Small-Scale Studies (Section 4) includes unnecessary filler phrases like "in order to gain further insight on," which slows the reader down. Additionally, the section title "Small-scale Studies" is slightly informal compared to the rest of the paper; "Small-Scale Experiments" would be more consistent.

In the Related Work section, the transition between critiquing Landmark Attention (LMK-Attn) and justifying the use of HoPE is abrupt. The authors jump from comparing their method to LMK-Attn to stating they adopted HoPE inspired by HSA without a clear bridging thought. Separating these points into distinct paragraphs or sentences would clarify the logical progression.

Finally, there are minor grammatical and stylistic issues in the Conclusion. The heading "Limitation and Future works" should be "Limitations and Future Work" to match standard academic conventions. The passive construction regarding the Q-Cal mechanism is also weaker than a direct statement of the unknown mechanism.

The abstract could be tightened to be more punchy and self-contained, specifically by simplifying the description of the results and ensuring the core mechanism (hierarchical factorization/landmark tokens) is named explicitly rather than just the acronym.

Overall, these are fixable prose issues that do not affect the scientific validity but, if addressed, would make the paper significantly easier to read and more professional.
