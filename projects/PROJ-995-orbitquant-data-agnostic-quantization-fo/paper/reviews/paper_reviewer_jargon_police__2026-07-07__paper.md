---
action_items:
- id: e5558351fc80
  severity: writing
  text: 'Section 1 (Introduction) and Section 2 (Methodology) use the acronym ''RPBH''
    (Randomized Permuted Block-Hadamard) multiple times before it is explicitly defined.
    The term appears in the abstract and intro without expansion. Define it at first
    use: ''randomized permuted block-Hadamard (RPBH) rotation''.'
- id: 01a005dcd4c7
  severity: writing
  text: Section 2.3 (RPBH) introduces the symbol `h` in Equation 5 and the text ('where
    h is the largest power of two...') without defining it in the notation section
    or immediately preceding the equation. Define `h` as the block size parameter
    where it first appears in the text or equation context.
- id: 4d1af0c36dba
  severity: writing
  text: 'Section 3.1 (Setup) and Table 1 use the notation ''W4A4'', ''W2A4'', etc.,
    without defining the convention. While common in quantization, an adjacent-field
    reader may not know ''W'' stands for weight bits and ''A'' for activation bits.
    Add a brief gloss at first use: ''W4A4 (4-bit weights, 4-bit activations)''.'
- id: acbbb91f48ca
  severity: writing
  text: "Section 2.3 mentions 'Rademacher sign diagonal' and 'Walsh\u2013Hadamard\
    \ matrix' without a one-sentence operational definition for a reader outside randomized\
    \ linear algebra. Briefly clarify: 'Rademacher signs (random \xB11 values)' and\
    \ 'Walsh\u2013Hadamard matrix (a structured orthogonal matrix with \xB11 entries)'."
- id: 050b14dc547c
  severity: writing
  text: 'Section 4 (Ablations) and Table 3 refer to ''Full RHT'' and ''Block-RHT''
    without defining these acronyms. Define them at first use: ''Full Randomized Hadamard
    Transform (RHT)'' and ''Block-Randomized Hadamard Transform (Block-RHT)''.'
artifact_hash: d056dc4f21ae1b95e98f52ede135ede40ce7ffad195ba83894f4cf9d35e33f1a
artifact_path: projects/PROJ-995-orbitquant-data-agnostic-quantization-fo/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-07T04:53:02.638542Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The paper is generally well-written for a specialized audience, but it relies on several acronyms and notation conventions that are introduced without explicit definition, creating minor barriers for a competent reader from an adjacent field (e.g., a computer vision researcher not specializing in quantization or randomized linear algebra).

The primary issue is the premature use of the acronym **RPBH** (Randomized Permuted Block-Hadamard). It appears in the Abstract, Introduction, and Methodology sections before the full phrase is ever spelled out. While the full phrase appears in the caption of Figure 2, the acronym is used in the main text (e.g., Section 1, paragraph 3; Section 2.1) without a prior expansion. A reader skimming the text would encounter "RPBH" without knowing what it stands for until much later or by guessing.

Additionally, the notation **W4A4** (and similar variants like W2A4) is used extensively in the Results section and tables without a definition. While standard in the quantization subfield, an adjacent-field PhD might not immediately parse "W" as weight bits and "A" as activation bits. A brief parenthetical expansion at the first occurrence in Section 3.1 would resolve this.

The symbol **h** is introduced in Section 2.3 as the block size for the Hadamard transform but is not defined in the Notation subsection (Section 1.1) or immediately before Equation 5. While the text eventually explains it, the lack of a formal definition at the point of introduction forces the reader to infer the meaning from context.

Finally, terms like **Full RHT** and **Block-RHT** are used in the Ablation section (Section 4) without being defined as acronyms for "Randomized Hadamard Transform." Defining these at first use would ensure clarity.

These are minor, easily fixable issues that do not detract from the scientific contribution but would improve the self-containment of the paper for a broader technical audience.
