---
action_items:
- id: f95a2c4bac55
  severity: writing
  text: The manuscript relies heavily on specialized acronyms and domain-specific
    shorthand that are not defined at their first point of use, creating a barrier
    for non-specialist readers. First, the core contribution, ConAct, is introduced
    in Section 2 ("End-to-End Mobile GUI Agent with ConAct") without ever explicitly
    stating what the acronym stands for (presumably "Context-as-Action" based on the
    title and content). It appears in the abstract and introduction implicitly but
    lacks a formal definition
artifact_hash: 7ba9201f0f49d9384a35f3eca07d4fd8d448c0da222a8a4e9472044b7e857c18
artifact_path: projects/PROJ-781-memgui-agent-an-end-to-end-long-horizon/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T18:54:25.973288Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on specialized acronyms and domain-specific shorthand that are not defined at their first point of use, creating a barrier for non-specialist readers.

First, the core contribution, **ConAct**, is introduced in Section 2 ("End-to-End Mobile GUI Agent with ConAct") without ever explicitly stating what the acronym stands for (presumably "Context-as-Action" based on the title and content). It appears in the abstract and introduction implicitly but lacks a formal definition like "ConAct (Context-as-Action)". This forces the reader to guess the meaning.

Second, the term **ReAct** is used repeatedly (e.g., Introduction, Section 2, Table 2) as a standard noun ("ReAct-style prompting") without defining it as "Reasoning and Acting." While common in the sub-field, a general AI reader may not recognize it as a specific prompting framework.

Third, key evaluation metrics **MTPR** and **IRR** appear in Table 2 and the text without definition in the main body. The footnotes in the table define them, but the prose should introduce these terms (e.g., "Memory-Task Proficiency Ratio (MTPR)") before referencing them to ensure the results are interpretable without cross-referencing table footnotes.

Finally, **SFT** is used in Section 3 ("MemGUI-3K Dataset") and Table 1 without expansion. It should be written as "supervised fine-tuning (SFT)" at first mention. Similarly, **Pass@k** metrics are used throughout the results without a brief parenthetical explanation of the sampling strategy.

These omissions do not invalidate the science but significantly reduce the paper's accessibility to a broader audience. Defining these terms upon first use is a straightforward fix.
