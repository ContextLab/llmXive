---
action_items:
- id: fef7b6d4fb8d
  severity: writing
  text: "Section\u202F1 (Introduction) uses the term *Full\u2011Context Attention*\
    \ without definition; add a brief explanation (e.g., \u201CFull\u2011Context Attention\
    \ refers to attention mechanisms that jointly attend to all input frames simultaneously,\
    \ providing global context\u201D)."
- id: 1ff5841583cc
  severity: writing
  text: "The phrase *Bounded\u2011memory models* appears in the introduction and results\
    \ but is never explained; define it when first used (e.g., \u201Cmodels that limit\
    \ memory usage by processing inputs in chunks or using a fixed\u2011size cache\u201D\
    )."
- id: a6106ab01e12
  severity: writing
  text: "The abbreviation *GT* (ground truth) is used throughout the paper (e.g.,\
    \ \u201CGT depth/pose priors\u201D) without an explicit definition; introduce\
    \ the full form at first occurrence."
- id: 0afec2e30830
  severity: writing
  text: "The term *pseudo\u2011GT* is introduced in the abstract and later (e.g.,\
    \ \u201Ccurated pseudo\u2011GT outperforms noisy scaling\u201D) without clarification;\
    \ explain what pseudo\u2011GT means (e.g., \u201Chigh\u2011quality depth generated\
    \ by a teacher model and treated as ground\u2011truth for training\u201D)."
- id: ec0e2099c309
  severity: writing
  text: "In the model architecture (Section\u202F4.2) the concept of *scale tokens*\
    \ is mentioned but not described; add a short description of their role (e.g.,\
    \ \u201Clearnable tokens that predict a global metric scale for the scene\u201D\
    )."
- id: d5abcaf600ee
  severity: writing
  text: "Tables contain the abbreviation *OOM* (out\u2011of\u2011memory) without a\
    \ legend; add a footnote or caption note defining OOM for readers."
artifact_hash: 306c5e78aff3c136de96c4c6956084c3af89239f10c2fba4682734d1809d3475
artifact_path: projects/PROJ-634-https-arxiv-org-abs-2605-27367/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T21:42:18.989481Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The paper is technically solid and presents a valuable benchmark, but several domain‑specific abbreviations and coined terms are introduced without definition, which can impede a competent reader from an adjacent field. Adding concise explanations for *Full‑Context Attention*, *Bounded‑memory models*, *GT*, *pseudo‑GT*, and *scale tokens* will make the manuscript self‑contained. Also, clarify the *OOM* label in tables. These relatively minor wording fixes will improve accessibility without affecting the scientific contributions.
