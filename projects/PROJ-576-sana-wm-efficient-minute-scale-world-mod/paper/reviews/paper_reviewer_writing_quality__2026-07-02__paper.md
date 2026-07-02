---
action_items:
- id: d553b59ecce6
  severity: writing
  text: Remove all author-specific debug macros (e.g., \cjs, \enze, \yy, \jc, \jy,
    \cai, \crh, \muyang, \haozhe, \haoyi) and the \tbd, \nan, \ph, \change, \bst,
    \snd commands from the final manuscript. These are clearly internal collaboration
    tools and must not appear in a public preprint.
- id: 83aeea978dc5
  severity: writing
  text: In Section 3 (Method), the phrase 'From Token-wise GDN to Frame-wise GDN'
    introduces a subsection but the text immediately following it jumps into equations
    without a clear transitional sentence explaining the motivation for the shift
    in granularity. Add a brief sentence bridging the token-level definition to the
    frame-level adaptation.
- id: ba6fe0e3a0ee
  severity: writing
  text: In Section 5 (Experiments), the sentence 'Note that the attention-sink variant
    means that we use the first latent frame as the attention sink...' is grammatically
    clunky and slightly ambiguous. Rephrase for clarity, e.g., 'In the attention-sink
    variant, the first latent frame serves as the global attention sink, while local
    window attention is applied to softmax layers to maintain constant memory consumption.'
artifact_hash: e5cefeb8f5a622284bf4bd8a2b4800bf995401cb7708f8533b8b272aa0c905d4
artifact_path: projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:42:59.691719Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_writing_quality
score: 0.0
verdict: minor_revision
---

The manuscript demonstrates a high level of technical sophistication, and the writing is generally clear and professional. However, there are specific areas where the text requires polishing to meet the standards of a final public preprint.

First, the LaTeX source contains numerous author-specific debug macros (e.g., `\cjs`, `\enze`, `\yy`, `\jc`, `\jy`, `\cai`, `\crh`, `\muyang`, `\haozhe`, `\haoyi`) and placeholder commands (`\tbd`, `\nan`, `\ph`, `\change`, `\bst`, `\snd`). These are clearly internal collaboration tools intended for the drafting phase. Their presence in the final manuscript is unprofessional and distracting. All such macros must be removed, and any text wrapped in them must be finalized or deleted before publication.

Second, in Section 3 (Method), the transition between the definition of token-wise GDN and the introduction of frame-wise GDN is abrupt. The subsection header "From Token-wise GDN to Frame-wise GDN" is followed immediately by the equation for token-wise GDN, then a paragraph explaining the limitations, and then the frame-wise equation. A brief transitional sentence is needed to explicitly state *why* the shift to frame-wise scanning is necessary for video modeling (e.g., to reduce the recurrent state update frequency from every token to every frame, thereby improving efficiency).

Third, in Section 5 (Experiments), under "Deployment efficiency path," the sentence "Note that the attention-sink variant means that we use the first latent frame as the attention sink with local window attention on softmax attention layers only, so that the memory consumption remains constant" is grammatically awkward and slightly confusing. It mixes the definition of the variant with its mechanism and result in a single, dense clause. Rephrasing this to clearly separate the mechanism (using the first frame as a sink) from the outcome (constant memory) would improve readability.

Finally, while the flow is generally good, some sentences in the Introduction are quite long and dense. For instance, the sentence beginning "Recent open-source systems achieve minute-scale..." could be split to improve readability. Overall, the paper is well-written but requires these specific edits to ensure clarity and professionalism.
