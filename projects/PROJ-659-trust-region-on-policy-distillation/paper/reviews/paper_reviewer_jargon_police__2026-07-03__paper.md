---
action_items:
- id: 9cc73974256c
  severity: writing
  text: Define 'SoG' (Student of Generation) and 'ToG' (Teacher of Generation) at
    first use in Section 3.1. The acronyms are introduced without definition, relying
    on reader inference from context.
- id: 7f4d7245fd84
  severity: writing
  text: Replace 'SoTA' with 'state-of-the-art' in the Abstract and Section 5.1. Acronyms
    for common phrases should be spelled out on first occurrence to aid non-specialist
    readers.
- id: d26fc1af8ca3
  severity: writing
  text: Define 'AIME', 'AMC', 'GPQA', 'MMLU', and 'IFBench' at their first mention
    in Section 5.2 or the Introduction. Currently, these benchmark acronyms are used
    without expansion, assuming domain familiarity.
- id: 84d7152b07fb
  severity: writing
  text: Clarify the term 'mid-training' in the Limitations section. This is not a
    standard, universally defined term in the field and requires a brief explanation
    of what stage of the pipeline it refers to.
artifact_hash: 74f03d7ab60f5026cfa7c71878897ef40634611691a4c76f5e68e8e21f3101c9
artifact_path: projects/PROJ-659-trust-region-on-policy-distillation/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T18:41:55.609282Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on domain-specific acronyms and shorthand that are not defined upon first use, creating barriers for readers outside the immediate sub-field of on-policy distillation.

In Section 3.1 ("Distillation for Language Models"), the authors introduce "teacher of generations (ToGs)" and "student of generations (SoGs)" but immediately switch to using the acronyms "ToG" and "SoG" without explicitly defining the acronym form (e.g., "ToG" vs "ToGs"). While the context is clear to an expert, a general reader may stumble. Similarly, in the Abstract and Section 5.1, the term "SoTA" is used repeatedly. This should be expanded to "state-of-the-art" at the first instance.

Furthermore, the experimental section (Section 5.2) is dense with benchmark acronyms—AIME, AMC, GPQA, MMLU, IFBench, LCB—none of which are expanded in the text. While these are standard in the LLM community, a paper claiming broad applicability should define them (e.g., "American Invitational Mathematics Examination (AIME)") to ensure accessibility.

Finally, the "Limitations" section mentions "mid-training" as a necessary stage. This is a non-standard term in the broader machine learning literature and is used without definition, potentially confusing readers regarding the specific training phase being referenced.

These issues are minor in terms of scientific validity but significant for readability and inclusivity. The authors should perform a pass to expand all acronyms at their first occurrence and define non-standard terminology.
