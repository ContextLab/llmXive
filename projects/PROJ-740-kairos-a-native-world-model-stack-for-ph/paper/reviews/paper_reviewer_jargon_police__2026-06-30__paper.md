---
action_items:
- id: d0fbeb545b81
  severity: science
  text: 'The manuscript suffers from severe jargon overuse, creating a barrier to
    entry for non-specialist readers and obscuring the core contributions. The term
    "Physical AI" is used repeatedly as a proper noun (e.g., Abstract, Introduction,
    Conclusion) without a single definition, forcing the reader to guess its specific
    scope versus general robotics or embodied AI. Similarly, critical architectural
    components are introduced via acronyms without expansion: "CEDC" (Cross-Embodiment
    Data Curriculum) and'
artifact_hash: 926e7dfe86ab0c8e4b8d20a90a842eec681ad7b82ae76075a7b3082533c6260d
artifact_path: projects/PROJ-740-kairos-a-native-world-model-stack-for-ph/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T11:54:55.236014Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: full_revision
---

The manuscript suffers from severe jargon overuse, creating a barrier to entry for non-specialist readers and obscuring the core contributions. The term "Physical AI" is used repeatedly as a proper noun (e.g., Abstract, Introduction, Conclusion) without a single definition, forcing the reader to guess its specific scope versus general robotics or embodied AI. Similarly, critical architectural components are introduced via acronyms without expansion: "CEDC" (Cross-Embodiment Data Curriculum) and "MoT" (Mixture-of-Transformers) appear in the Abstract and Introduction without being spelled out, violating basic technical writing standards.

The word "native" is abused as a buzzword, appearing in phrases like "native world model stack," "native knowledge injection," and "native understanding-generation-prediction." This repetition adds no semantic value; "intrinsic" or "built-in" would be clearer. In the Model section, specific attention mechanisms like "GLA" and "DSWA" are deployed without definition, assuming the reader is already an expert in the authors' specific nomenclature. Furthermore, the phrase "first-order modeling condition" in the Abstract is unnecessarily abstract; "primary constraint" conveys the same meaning with greater clarity.

In the Inference section, terms like "DiT-Cache" and "TeaCache" are mentioned as if they are universally known, yet they are likely specific to this implementation or a very narrow sub-field. The verb "evolutionize" in the Conclusion is a non-standard neologism that should be replaced with "evolve" or "transform." Finally, foundational training concepts like "Flow Matching" and "DPO" are used without definition in the Training section. To meet publication standards, the authors must define every acronym at first use, replace buzzwords with precise terminology, and ensure that specialized concepts are explained for a broader scientific audience.
