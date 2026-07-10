---
action_items:
- id: 4ff55e7ed963
  severity: writing
  text: 'Section 1, Introduction: The acronym ''LLM'' appears in ''large language
    models (LLM)'' but is not expanded at first use in the body text (it is only defined
    in the abstract). Expand to ''large language models (LLMs)'' at the first occurrence
    in Section 1 to ensure self-containment for adjacent-field readers.'
- id: 9ae33c34e98f
  severity: writing
  text: "Section 2, Model Architecture: The symbol '\u03BA' is introduced in the equation\
    \ for timestep-balanced gradient reweighting (Section 5, subsection On-Policy\
    \ GRPO Training) without a definition in the surrounding text. It is unclear if\
    \ this is a gain factor, a temperature, or a constant. Add a clause defining \u03BA\
    \ (e.g., 'where \u03BA_k is the transition gain at step k') immediately after\
    \ the equation."
- id: a120966eddf1
  severity: writing
  text: 'Section 2, Model Architecture: The term ''MoE 13B-A1.4B-E128'' is used as
    a specific model identifier in Section 2.3 without a prior gloss explaining the
    naming convention (Total Params - Active Params - Expert Count). Define this convention
    once when first introduced to prevent confusion for readers unfamiliar with this
    specific shorthand.'
- id: 193700cbcea7
  severity: writing
  text: 'Section 4, Infrastructure: The acronym ''FSDP'' is used in ''fully sharded
    data parallelism (FSDP)'' but the expansion is slightly non-standard (usually
    ''Fully Sharded Data Parallel'' without the ''ism''). While minor, ensure the
    expansion matches the standard literature or define it explicitly as ''Fully Sharded
    Data Parallelism'' to avoid ambiguity for readers from adjacent distributed systems
    fields.'
- id: 46bbb3f3496c
  severity: writing
  text: 'Section 5, Training: The term ''CPS'' (Coefficients-Preserving Sampling)
    is introduced in the context of GRPO training. While the full name is given, the
    acronym ''CPS'' is not standard in the broader diffusion literature (unlike DDIM
    or SDE). Ensure the definition is prominent and perhaps add a brief parenthetical
    explaining its specific role (e.g., ''...CPS (a DDIM-style transition that preserves
    noise coefficients)...'') to distinguish it from other sampling methods.'
artifact_hash: 9ee70f69980a19ab6b09b1ef85c408bba9d6c20db5c959c0faf89cac5e30112c
artifact_path: projects/PROJ-1026-scaling-mixture-of-experts-video-pretrai/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-10T03:03:24.945177Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The paper is generally well-structured and uses standard terminology for the diffusion and transformer communities (e.g., "DiT," "RoPE," "SwiGLU," "FlashAttention"). However, there are a few instances where acronyms or notation are introduced without sufficient definition for a competent reader from an adjacent field (e.g., a systems researcher or a computer vision specialist not deeply embedded in the specific MoE video generation subfield).

Specifically, the acronym "LLM" appears in the Introduction without being spelled out in the body text, relying on the abstract for the definition, which breaks the self-contained nature of the section. Additionally, the symbol `κ` in the GRPO training equations (Section 5) is used without a textual definition, forcing the reader to infer its meaning from the equation structure alone. The specific naming convention for model variants (e.g., "MoE 13B-A1.4B-E128") is also used without an explicit gloss of the format, which could be opaque to outsiders. Finally, while "CPS" is defined, its specific operational distinction from standard sampling methods could be clarified with a brief explanatory clause to ensure immediate understanding.

Addressing these minor gaps will ensure the paper is fully accessible to the target "adjacent-field PhD" audience without requiring them to cross-reference the abstract or guess at notation.
