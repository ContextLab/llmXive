---
action_items:
- id: bc63b227fa7c
  severity: writing
  text: 'Add missing bibliography entries for cited keys: meng2022locating, Chrisman1992,
    kaelbling1998planning, baldelli2026, galashov2025, grazzi2025, lin2025forgetting,
    leviathan2025selective, beltagy2020longformer, oncescu2026, olsson2022context,
    hochreiter1997long.'
- id: 5e11edd5679d
  severity: science
  text: Verify that claims attributed to missing citations (e.g., state tracking failures
    in multi-turn conversations) are supported by the actual content of the referenced
    works once added.
artifact_hash: 924b893a4650c3044c8ebca795788f41846a7a72e06ec4cbf52905fb73429333
artifact_path: projects/PROJ-746-the-topological-trouble-with-transformer/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-26T10:25:48.968038Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

This review focuses on the accuracy of factual claims and the integrity of citations. The manuscript makes numerous specific claims about transformer limitations, state tracking, and architectural capabilities that rely heavily on external literature. However, a significant number of these citations are missing from the provided bibliography file (`topological_trouble.bib`), rendering the claims unverifiable.

In the Introduction (lines 105-106), the claim that transformers "postponing the selection of relevant data until required for inference" cites `\citep{meng2022locating}`, which is absent from the bibliography. Similarly, the definition of "belief state" (lines 123-124) cites `Chrisman1992` and `kaelbling1998planning`, neither of which are present. In the State Tracking section, the footnote regarding Gemini 3 failures (lines 145-147) references `\citet{baldelli2026}`, which is also missing.

Further issues appear in the Recurrent Architectures section. The claim that some latent-thought models "do not" track state cites `galashov2025` (line 335), which is not in the bib. In the Promising Directions section, claims about Delta Net eigenvalues cite `grazzi2025` (line 435), and claims about new attention forms cite `lin2025forgetting`, `leviathan2025selective`, and `beltagy2020longformer` (line 442), all of which are missing. Additionally, `olsson2022context` (line 118) and `hochreiter1997long` (line 112) are cited but not listed.

While the theoretical argument is coherent, the accuracy of the claims cannot be validated without these sources. The missing citations suggest incomplete bibliography management. If these references are critical to the core argument (e.g., formal proofs of state tracking limitations), their absence undermines the scientific validity of the claims. Please add all missing entries to the bibliography and verify that the text accurately reflects the content of those sources. This is a writing-level fix but impacts the scientific credibility of the paper.
