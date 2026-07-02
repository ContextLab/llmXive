---
action_items:
- id: 7cbb2cabdd32
  severity: writing
  text: "The manuscript relies heavily on domain-specific acronyms and mathematical\
    \ shorthand that hinder accessibility for a broader robotics or computer science\
    \ audience. First, the Abstract introduces three major acronyms\u2014VLA (vision-language-action\
    \ models), WAM (video world-action models), and GAM (Geometric Action Model)\u2014\
    without defining them. While GAM is defined, VLA and WAM are used immediately.\
    \ The Introduction defines VLA and WAM but repeats the acronym GAM without re-defining\
    \ it in the context"
artifact_hash: 2b47a226fbf60e77bf3630e010af6d066f9a3ac0ebb39463048a80ab1f66b524
artifact_path: projects/PROJ-718-geometric-action-model-for-robot-policy/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T20:59:33.252112Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on domain-specific acronyms and mathematical shorthand that hinder accessibility for a broader robotics or computer science audience. 

First, the Abstract introduces three major acronyms—**VLA** (vision-language-action models), **WAM** (video world-action models), and **GAM** (Geometric Action Model)—without defining them. While **GAM** is defined, **VLA** and **WAM** are used immediately. The Introduction defines **VLA** and **WAM** but repeats the acronym **GAM** without re-defining it in the context of the Abstract's summary. The term **GFM** (Geometric Foundation Model) is also introduced in the Abstract without definition. Standard practice requires defining these at their very first occurrence in the Abstract or the first paragraph of the Introduction.

Second, the phrase "($\uparrow$9.7%p)" in the Introduction and Section 4.1 uses the symbol 'p' to denote percentage points. This is non-standard and potentially confusing; "percentage points" should be written out or the symbol 'pp' used if space is strictly limited, though 'p' is generally discouraged in formal writing.

Third, technical architectural terms are used without definition. In Section 3, the **DPT** head is mentioned without expansion (Dense Prediction Transformer). In Section 4.4, **key-value caching** is referenced as a standard inference technique without explanation. Additionally, the notation **SE(3)** in Section 3 is used without a brief textual explanation (e.g., "3D rigid body transformations"), which may alienate readers from control backgrounds who are less familiar with Lie group notation.

Finally, the term **block-causal self-attention** in Section 4.2 is a specific variant of attention mechanisms. While the paper cites a source, a brief parenthetical explanation (e.g., "attention that prevents future leakage within blocks") would improve clarity for non-specialists. These changes are necessary to ensure the paper's contributions are accessible beyond the immediate sub-field of geometric foundation models.
