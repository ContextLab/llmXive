---
action_items:
- id: ddb946f7be62
  severity: writing
  text: Define 'CUA' (Computer-Use Agent) at first use in Section 2.2. The text currently
    uses 'CUA' and 'GCUA' without explicitly spelling out the acronym 'Computer-Use
    Agent' in the main body, relying on the reader to infer it from context or the
    appendix.
- id: 8a46509537a8
  severity: writing
  text: Replace the acronym 'GCUA' with 'Generalist Computer-Use Agent' or 'generalist
    agent' throughout the text. The term 'GCUA' is introduced but then used repeatedly
    as a standalone noun (e.g., 'evaluate all agent systems in GCUA configuration'),
    which is non-standard and excludes non-specialist readers.
- id: 82b4cb2822e2
  severity: writing
  text: Define 'MCP' (Model Context Protocol) at first use in Section 2.2 and Appendix
    A.1. The text mentions 'CUA MCP bridge' and 'MCP server' without defining the
    protocol, assuming reader familiarity with a specific industry standard.
- id: 737e24485110
  severity: writing
  text: Replace 'harness' with 'orchestration framework' or 'agent framework' in the
    main text. While 'harness' is common in testing, its use to describe the entire
    agent loop (e.g., 'mainstream harness implementations') is jargon-heavy and less
    accessible than 'framework' or 'system'.
- id: 1749014ca70b
  severity: writing
  text: Define 'SOC' (Standard Occupational Classification) at first use in the Abstract
    and Section 2.2. The text references 'SOC 2018' immediately without spelling out
    the classification system, which is not universally known outside labor economics
    or specific US government contexts.
- id: 5176d5f8d0c0
  severity: writing
  text: Replace 'backbone' with 'foundation model' or 'base model' in the main text.
    The term 'backbone' (e.g., 'backbone configurations', 'fixed backbone') is technical
    jargon from deep learning architecture that may confuse readers from other domains.
- id: 808400da970e
  severity: writing
  text: Define 'QC' (Quality Control) at first use in Figure 2 caption. The caption
    mentions 'Quality Control (QC) Process' but the acronym 'QC' is used later in
    the text without re-definition or context for non-industry readers.
artifact_hash: 326ff13c3b60fc13345363439d3391333425191b488bb3324c7d31083263c3e8
artifact_path: projects/PROJ-688-agents-last-exam/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T03:12:51.265463Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on domain-specific acronyms and technical shorthand that obscure meaning for a general scientific audience. The most critical issue is the introduction and subsequent overuse of the acronym **GCUA** (Generalist Computer-Use Agent). While the full term is defined once, the paper immediately shifts to using "GCUA" as a standalone noun (e.g., "evaluate all agent systems in GCUA configuration," "GCUA reference"). This creates a barrier for readers not deeply embedded in the specific "computer-use agent" sub-field. The term should be replaced with "generalist agent" or the full phrase to improve readability.

Similarly, **CUA** (Computer-Use Agent) and **MCP** (Model Context Protocol) are used without explicit definition in the main text. "CUA" appears in the phrase "CUA MCP bridge" in Section 2.2 and Appendix A.1, assuming the reader knows both the agent type and the protocol. "MCP" is a specific industry standard that requires a brief explanation or citation upon first mention.

The term **harness** is used extensively to describe the agent's orchestration layer (e.g., "mainstream harness implementations," "harness sweeps"). While standard in software testing, in this context it functions as jargon for "agent framework" or "orchestration system." Replacing "harness" with "framework" would make the text more accessible.

Additionally, **SOC** (Standard Occupational Classification) is referenced in the Abstract and Section 2.2 without being spelled out. While "O*NET" is also an acronym, it is often more recognizable in this context; however, "SOC" is a specific US government taxonomy that should be defined. Finally, **backbone** is used to refer to the underlying foundation model (e.g., "fixed backbone," "backbone configurations"). This is deep learning jargon that should be replaced with "foundation model" or "base model" to align with broader AI literature and aid non-specialist readers.

These changes are purely stylistic and do not affect the scientific validity of the work, but they are necessary to ensure the paper is accessible to the broader AI community and interdisciplinary readers.
