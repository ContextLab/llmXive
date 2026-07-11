---
action_items:
- id: 95b4c484fb89
  severity: writing
  text: 'Abstract & Section 1: The acronym ''ZS-CAR'' is used before being defined.
    Define ''Zero-Shot Compositional Action Recognition (ZS-CAR)'' at its first occurrence
    in the Abstract or Introduction.'
- id: 3a7c9e852145
  severity: writing
  text: 'Section 1 & 3: The acronyms ''FSP'' and ''FCP'' are used in the Introduction
    and Section 3 without prior expansion. Define ''False Seen Prediction (FSP)''
    and ''False Co-occurrence Prediction (FCP)'' at their first occurrence in Section
    3.2.'
- id: 7575be79c42b
  severity: writing
  text: 'Section 1 & 4: The acronyms ''CPR'' and ''TORC'' are introduced in the Introduction
    and used in Section 4 without expansion. Define ''Co-occurrence Prior Regularization
    (CPR)'' and ''Temporal Order Regularization for Composition (TORC)'' at their
    first occurrence in Section 4.'
- id: 7896a7a38cf5
  severity: writing
  text: "Section 3.2: The symbol 'Dcg' (or $\\Delta_{\text{CG}}$) is used in the text\
    \ and equations. Ensure 'Compositional Gap ($\\Delta_{\text{CG}}$)' is explicitly\
    \ defined with the symbol before Equation 2."
- id: 97859728fce0
  severity: writing
  text: 'Section 5.1: The abbreviation ''H.M.'' is used in the text and tables without
    definition. Define ''Harmonic Mean (H.M.)'' at its first occurrence in Section
    5.1.'
- id: ecfbd454d8f1
  severity: writing
  text: 'Section 5.1: The dataset names ''Sth-com'' and ''EK100-com'' are used as
    shorthand. Define ''Sth-com (Something-Something V2 compositional benchmark)''
    and ''EK100-com (EPIC-KITCHENS-100 compositional benchmark)'' at their first occurrence.'
artifact_hash: f098ae707662ea7ce696ff8b8606006fdddb80c25be82361ec114d13c9a397ed
artifact_path: projects/PROJ-1037-why-can-t-i-open-my-drawer-mitigating-ob/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-11T04:20:03.360480Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The paper is generally well-structured and the technical content is accessible to a researcher in a neighboring field (e.g., video understanding or general machine learning). However, there are several instances where acronyms and dataset shorthand are used before being defined, which creates unnecessary friction for an adjacent-field reader.

Specifically, the acronyms ZS-CAR, FSP, FCP, CPR, and TORC appear in the Abstract or Introduction before their full names are provided. While the full names are eventually given in the body text, the standard convention is to define an acronym at its very first use. For example, "ZS-CAR" appears in the first sentence of the Abstract without expansion. Similarly, "FSP" and "FCP" are introduced in the Introduction as if they are standard terms, but they are specific diagnostic metrics defined later in Section 3.2.

The dataset names "Sth-com" and "EK100-com" are also used frequently without initial expansion. While "Something-Something" and "EPIC-KITCHENS" are well-known, the specific "-com" suffix denotes a specific compositional split/benchmark created or repurposed by the authors, which is not immediately obvious to an outsider.

Finally, the symbol $\Delta_{\text{CG}}$ (referred to as Dcg in some text) is used in equations and text. While the concept of a "gap" is intuitive, the specific notation should be explicitly defined alongside the term "Compositional Gap" when first introduced.

Addressing these points by ensuring every acronym and specialized symbol is defined at its first occurrence will make the paper significantly more self-contained and accessible.
