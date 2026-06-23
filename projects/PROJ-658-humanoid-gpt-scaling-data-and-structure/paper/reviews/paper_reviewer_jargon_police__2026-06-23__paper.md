---
action_items:
- id: 81370694c5ed
  severity: writing
  text: Define every acronym on first use (e.g., AGI, MLP, PPO, DAgger, HME, G1, SR,
    MPJPE, MPJVE, MPKPE).
- id: 02e3cd53d292
  severity: writing
  text: "Replace overloaded buzzwords such as \u201Cscaling\u201D, \u201Czero\u2011\
    shot\u201D, \u201Cfoundation model\u201D, \u201Cemergent\u201D, and \u201Cscience\
    \ of scale\u201D with concrete descriptions of what is actually being increased\
    \ or achieved."
- id: f20f6be3b31f
  severity: writing
  text: Remove or simplify decorative macros (e.g., \red{}, \blue{}, colored bold
    text) that add visual noise without adding meaning for readers.
- id: 6f62eb3d7f24
  severity: writing
  text: "Provide plain\u2011language explanations for technical terms like \u201C\
    causal attention\u201D, \u201CGPT\u2011style Transformer\u201D, and \u201CHarmonic\
    \ Motion Embedding (HME)\u201D to make the paper accessible to readers outside\
    \ the robotics/ML sub\u2011community."
- id: 25cb6fe9892c
  severity: writing
  text: "Avoid excessive use of check\u2011mark symbols (\\checkmark) in tables; replace\
    \ with clear textual indicators (e.g., \u201Cyes\u201D/\u201Cno\u201D)."
artifact_hash: 11a83a092083d485002512d3e56d130e02aef8501fdca7259786be2bc34086fd
artifact_path: projects/PROJ-658-humanoid-gpt-scaling-data-and-structure/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-23T13:00:38.697273Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript is rich in technical content but suffers from pervasive jargon and undefined acronyms that hinder accessibility for readers who are not specialists in humanoid robotics or large‑scale language‑model literature.

1. **Acronym Overload** – Throughout the paper (e.g., Section 1, lines 12‑20) terms such as *AGI*, *MLP*, *PPO*, *DAgger*, *HME*, *G1*, *SR*, *MPJPE*, *MPJVE*, and *MPKPE* appear without an explicit definition at first occurrence. This forces the reader to infer meanings from context or external sources, violating the principle of self‑contained exposition.

2. **Buzzword Saturation** – The word “scaling” is used repeatedly (Abstract, Introduction, Table 1 caption, Section 3) to describe both data size and model capacity, yet the manuscript rarely quantifies what “scaling” entails beyond raw frame counts. Phrases like “zero‑shot”, “foundation model”, “emergent”, and “science of scale” are introduced as if they convey substantive technical insight, but they function more as marketing jargon. Replacing them with precise statements (e.g., “trained on 2 billion motion frames”, “evaluated without task‑specific fine‑tuning”) would improve clarity.

3. **Decorative Macros and Color Coding** – The source defines numerous macros for colored bold text (e.g., `\red{}`, `\blue{}`, `\green{}`) and uses them extensively in tables and the supplementary section. While visually striking in the PDF, these styles add no semantic value and can distract readers, especially in printed or screen‑reader contexts. Stripping these decorations or limiting them to figure captions would streamline the narrative.

4. **Symbolic Check‑Marks** – Table 1 and Table 2 employ LaTeX check‑mark symbols (`\checkmark`) to indicate capabilities. For a broad audience, explicit textual labels (“yes”/“no”) are more immediately understandable and improve accessibility for assistive technologies.

5. **Technical Term Explanations** – Concepts such as “causal attention”, “GPT‑style Transformer”, and the newly introduced “Harmonic Motion Embedding (HME)” are mentioned without lay explanations. A brief, non‑technical description (e.g., “causal attention ensures the model only uses past observations when predicting the next control command”) would make the paper approachable to readers from adjacent fields such as control theory or biomechanics.

6. **Section Referencing** – The manuscript frequently references internal sections (e.g., “see Sec 3.2”) without providing a short summary of the referenced content. Adding a one‑sentence preview when citing a section would help readers maintain context without flipping pages.

Addressing these points will substantially lower the entry barrier for interdisciplinary readers and improve the overall readability of the paper without altering its scientific contributions.
