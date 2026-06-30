---
action_items:
- id: 85d8cb5aaf3e
  severity: writing
  text: The manuscript relies heavily on internal jargon and undefined acronyms that
    hinder accessibility for non-specialist readers. First, the core contribution,
    ConAct (Context-as-Action), is introduced via the macro \conact in the Abstract
    without a clear, plain-English definition for the general audience. The term "Context-as-Action"
    itself is a coined phrase that requires immediate, explicit definition upon first
    mention, rather than assuming the reader understands the "first-class action"
    metapho
artifact_hash: 7ba9201f0f49d9384a35f3eca07d4fd8d448c0da222a8a4e9472044b7e857c18
artifact_path: projects/PROJ-781-memgui-agent-an-end-to-end-long-horizon/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T19:34:06.417332Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on internal jargon and undefined acronyms that hinder accessibility for non-specialist readers. 

First, the core contribution, **ConAct** (Context-as-Action), is introduced via the macro `\conact` in the Abstract without a clear, plain-English definition for the general audience. The term "Context-as-Action" itself is a coined phrase that requires immediate, explicit definition upon first mention, rather than assuming the reader understands the "first-class action" metaphor. Similarly, **MemGUI-Agent** (`\ourmethod`) is used repeatedly without a full expansion in the Abstract.

Second, the paper uses metaphorical jargon such as "**prompt explosion**" (Abstract, Introduction) to describe context length issues. This term is dramatic but imprecise; "excessive context length" or "context bloat" would be clearer. The concept of "**folding**" (e.g., "folded action history," "span-level folds" in Sections 3.1, 3.3, and 5.3) is used as a technical term without a plain-language equivalent. While "folding" is a known concept in some contexts, here it functions as internal shorthand for "compression" or "summarization," which should be used to ensure clarity.

Third, several critical acronyms are used without definition. **IRR** (Information Retention Rate) and **MTPR** (Memory-Task Proficiency Ratio) appear in Section 5.1 and Table 2 without being spelled out. **SFT** (Supervised Fine-Tuning) is used in the Abstract and Section 4 without expansion. **ReAct** is used as a proper noun for a prompting style; while common in the field, it should be briefly defined as "Reasoning and Acting" for broader accessibility.

Finally, terms like "**zero-shot**" (Section 5.2) and "**backbone**" (Section 4) are standard ML jargon. While acceptable in a technical paper, the frequency of their use without context suggests a target audience that is already deeply embedded in the field. Replacing "zero-shot" with "without fine-tuning" in key explanatory sentences would improve readability. The paper needs a pass to replace these internal terms with their plain-language equivalents and to define all acronyms at first use.
