---
action_items:
- id: aa293f97af28
  severity: writing
  text: "The abstract contains three overlapping versions of the same paragraph (lines\
    \ 71\u2011108). Remove the duplicated text and keep a single concise abstract."
- id: a9cf59ae20b8
  severity: writing
  text: "In the Introduction, the first sentence is overly long and mixes several\
    \ ideas (lines 115\u2011122). Split it into two sentences for better readability."
- id: 1271eca111f5
  severity: writing
  text: "Several acronyms (e.g., KV\u2011Cache, RTN, SINQ) are introduced without\
    \ prior definition or consistent formatting (e.g., lines 138\u2011144, 210\u2011\
    215). Define each acronym on first use and use a uniform style."
- id: c7b099e1ff7f
  severity: writing
  text: "Figure captions are overly verbose and contain LaTeX commands that break\
    \ flow (e.g., Fig.\u202F1 caption lines 176\u2011186). Rewrite captions to be\
    \ self\u2011contained, clear, and free of internal references like \u2018Eq.~\\\
    ref{eq:decompose}\u2019 unless the equation is actually present."
- id: 8e340f9dff15
  severity: writing
  text: "The paper mixes British and American spelling (e.g., \u201Coptimise\u201D\
    \ vs. \u201Coptimize\u201D) and inconsistent capitalization of section headings\
    \ (e.g., \u2018Preliminaries\u2019 vs. \u2018Key Ideas\u2019). Standardize spelling\
    \ and heading style."
- id: ba75aa16ed0f
  severity: writing
  text: "The pseudo\u2011decode description (Section\u202F4.2, lines 260\u2011274)\
    \ repeats the same idea twice and uses informal phrasing such as \u2018we will\
    \ show\u2019. Rephrase to a more formal tone and eliminate redundancy."
- id: a8975de37612
  severity: writing
  text: "The \u2018Key Ideas\u2019 paragraph (lines 300\u2011312) uses a wrap\u2011\
    figure that interrupts the text flow and leaves a dangling reference to Fig.\u202F\
    2 without proper introduction. Relocate the figure or adjust the layout."
- id: 994f7d4689ee
  severity: writing
  text: "In the Methods section, the equation derivation (lines 340\u2011355) is dense\
    \ and lacks explanatory prose; add a brief narrative explaining each step."
- id: cb3473e8352a
  severity: writing
  text: "The conclusion (lines 560\u2011572) repeats results already presented in\
    \ tables; condense to a summary of contributions and future work."
- id: a2e95c8714a8
  severity: writing
  text: "The bibliography style is set to \u2018plain\u2019 but the .bbl file is empty,\
    \ leading to missing citations throughout the text. Ensure all references are\
    \ properly included."
artifact_hash: 41b8c942a61f2cf7279ecdca15cbc48d6d8be293f3b82fe8c5a5b6e8c4e01484
artifact_path: projects/PROJ-657-https-arxiv-org-abs-2606-03458/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-20T04:35:08.572964Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_writing_quality
score: 0.0
verdict: minor_revision
---

The manuscript is generally well‑structured and follows the NeurIPS template, but the writing suffers from several clarity and flow issues that hinder comprehension.

**Abstract** – The abstract currently contains three overlapping versions of the same paragraph (lines 71‑108). This redundancy makes it difficult for readers to grasp the core contribution quickly. A single, concise abstract of ~150 words should be retained, eliminating the commented‑out versions.

**Introduction** – The opening sentence (lines 115‑122) tries to convey test‑time scaling, memory bottlenecks, and KV‑Cache relevance all at once, resulting in a run‑on sentence. Splitting it into two sentences—one describing the scaling trend and another introducing the memory challenge—will improve readability. Additionally, the term “KV‑Cache quantization” is introduced without a brief definition; a short explanatory clause would help newcomers.

**Acronym Consistency** – Acronyms such as KV‑Cache, RTN (round‑to‑nearest), and SINQ appear multiple times (e.g., lines 138‑144, 210‑215) without consistent formatting or prior definition. Define each on first use and keep the style uniform (e.g., all caps, no hyphenation).

**Figures and Captions** – Captions for Fig. 1 and Fig. 2 (lines 176‑186, 210‑218) are overly long, embed LaTeX references (e.g., “Eq.~\ref{eq:decompose}”), and repeat information already in the main text. Captions should be self‑contained, succinct, and free of internal cross‑references unless the referenced element is immediately visible.

**Section Headings and Spelling** – The manuscript mixes British and American spelling (“optimise” vs. “optimize”) and shows inconsistent heading capitalization (e.g., “Preliminaries” vs. “Key Ideas”). Adopt a single spelling convention and follow the template’s title‑case style for all headings.

**Pseudo‑decode Description** – In Section 4.2 (lines 260‑274) the description of the pseudo‑decode evaluation repeats the same idea twice and uses informal phrasing (“we will show”). Rewriting this paragraph in a more formal tone and removing redundancy will make the methodology clearer.

**Layout Issues** – The wrap‑figure in the “Key Ideas” paragraph (lines 300‑312) interrupts the narrative flow and leaves a dangling reference to Fig. 2 without proper introduction. Consider moving the figure to a dedicated float or adjusting the text layout.

**Method Derivation** – The error decomposition (Eq. (2), lines 340‑355) is presented without sufficient explanatory prose. Adding a brief sentence before and after the derivation to guide the reader through the steps will aid understanding.

**Conclusion** – The conclusion (lines 560‑572) restates detailed quantitative results already shown in tables. It should instead summarise the main contributions, highlight the significance of variance‑normalised quantisation, and suggest future directions.

**References** – The bibliography is set to the ‘plain’ style but the .bbl file is empty, leading to missing citations throughout the text. Populate the bibliography to ensure all cited works appear correctly.

Addressing these points will substantially improve the manuscript’s clarity, flow, and overall readability, making the technical contributions more accessible to the broader audience.
