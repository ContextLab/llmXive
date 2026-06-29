---
action_items:
- id: b111e41f5bd3
  severity: writing
  text: "Abstract is dense; break the long sentence into two and clarify the meaning\
    \ of \u201Cfull\u2011shot, 10\u2011shot, 1\u2011shot\u201D."
- id: 8812fd382658
  severity: writing
  text: "In the Introduction, the phrase \u201Cmodels are benchmarked disjointly,\
    \ hindering direct comparison\u201D is vague \u2013 replace with a more precise\
    \ description of the fragmentation problem."
- id: f46446251ed5
  severity: writing
  text: "Figure captions (e.g., Fig.\u202F1, Fig.\u202F2) start with bold text but\
    \ lack a period after the closing brace; add a period for consistency."
- id: 420470c1c1a7
  severity: writing
  text: "Section\u202F3 (Methodology) contains a run\u2011on sentence: \u201CGENEB\
    \ probes frozen embeddings with logistic regression (max_iter=1000) in 1\u2011\
    shot, 10\u2011shot, and full\u2011data regimes (5 seeds: 13,\u202F17,\u202F42,\u202F\
    123,\u202F997).\u201D Split into two sentences for readability."
- id: a2f01abcec7c
  severity: writing
  text: "Throughout the manuscript, commas are sometimes missing after introductory\
    \ clauses (e.g., \u201CAfter removing the prokaryotic outlier \u2026 raises \u03C1\
    \ to 0.685\u201D). Insert commas to improve flow."
- id: 3f6085f587fe
  severity: writing
  text: "The use of \u201C\u2265\u201D and \u201C\u2264\u201D symbols in the text\
    \ (e.g., \u201C31/36 models show a \u22655\xD7 smaller model outperforming\u2026\
    \u201D) should be spelled out or placed in math mode for consistency."
- id: 5b075f6532e7
  severity: writing
  text: "In Table\u202F1 and Table\u202F2 captions, the term \u201Cmacro\u2011MCC\u201D\
    \ is introduced without definition; add a brief explanation of the metric on first\
    \ use."
- id: 8e677709b656
  severity: writing
  text: "The \u201CPractitioner Recommendations\u201D bullet list mixes model names\
    \ with performance numbers without clear separators; reformat as \u201CModel (size,\
    \ tokenization): performance metric\u201D."
- id: 3d51a7d3ed53
  severity: writing
  text: "Section\u202F4.2 (Architecture Effects) uses the phrase \u201CTransformer\u2011\
    decoder $+$0.149 macro\u2011MCC vs. Mamba\u201D \u2013 clarify that this is a\
    \ performance gain and not a mathematical addition."
- id: 2d6ee980a7a4
  severity: writing
  text: The conclusion repeats several points from the abstract verbatim; condense
    to avoid redundancy.
- id: 155719efc5f5
  severity: writing
  text: "Several abbreviations (e.g., \u201CMCC\u201D, \u201CSSM\u201D, \u201CBPE\u201D\
    ) are not defined at first appearance; add definitions."
- id: 449ef15bc9af
  severity: writing
  text: "In the Limitations section, the bullet points lack parallel structure; rewrite\
    \ so each starts with a gerund (e.g., \u201CExcluding long\u2011range tasks limits\u2026\
    \u201D, \u201CTask curation may contain noisy labels\u2026\u201D)."
- id: b07940929c21
  severity: writing
  text: "The bibliography entries have inconsistent formatting (some use \u2018arXiv\u2019\
    , others \u2018bioRxiv\u2019); standardize according to the journal\u2019s style."
artifact_hash: 043e93d2fab619e0251c0029f296fc31d53c712bc78a466a1a30d67af8b711e1
artifact_path: projects/PROJ-679-geneb-why-genomic-models-are-hard-to-com/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T01:36:59.373338Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_writing_quality
score: 0.0
verdict: minor_revision
---

The manuscript presents a valuable benchmark (GENEB) that evaluates a large collection of genomic foundation models across many tasks. From a writing‑quality perspective the paper is generally well organized, but several recurring issues hinder clarity and smooth reading.

The abstract packs multiple ideas into a single sentence, making it hard for readers to grasp the core contribution. Splitting it and explicitly defining “full‑shot, 10‑shot, 1‑shot” would improve accessibility. The introduction repeats the notion of “fragmented evaluation” without concrete examples; a brief illustration would ground the claim.

Figure captions (e.g., Fig. 1, Fig. 2) start with bold text but omit a period after the closing brace, breaking the journal’s style. Captions also sometimes contain technical shorthand (e.g., “MCC”) without prior definition; the first occurrence of each abbreviation should be expanded.

Methodology (Section 3) contains a run‑on sentence describing the probing protocol. Breaking it into two sentences and adding a comma after the parenthetical list of seeds would enhance readability. Similar comma omissions appear elsewhere, such as after introductory clauses (“After removing the prokaryotic outlier … raises ρ to 0.685”), which disrupts the flow.

Tables and their captions introduce metrics like “macro‑MCC” without explanation; a brief definition on first use would help non‑specialist readers. The “Practitioner Recommendations” bullet list mixes model names, sizes, and performance numbers without clear separators, making it difficult to parse. Reformatting each bullet as “Model (size, tokenization): performance metric” would resolve this.

Technical notation sometimes mixes plain text and math mode (e.g., “≥5× smaller model”). Consistently using LaTeX math mode or spelling out the comparison improves typographic consistency. In Section 4.2, the phrase “Transformer‑decoder $+$0.149 macro‑MCC vs. Mamba” could be misread as a mathematical addition; rephrase to “Transformer‑decoder outperforms Mamba by 0.149 macro‑MCC”.

The conclusion largely repeats the abstract verbatim. Condensing the conclusion to highlight new insights rather than restating earlier statements would avoid redundancy. Finally, the bibliography shows inconsistent formatting across entries (arXiv vs. bioRxiv citations). Aligning all references to a single style will give the paper a polished appearance.

Addressing these points will substantially improve the manuscript’s clarity, flow, and overall readability.
