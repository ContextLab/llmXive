---
action_items:
- id: d0ac344b2f37
  severity: writing
  text: "Replace vague buzzwords such as \u201Coperational substrate\u201D, \u201C\
    agentic systems\u201D, and \u201Charness interface\u201D with concrete descriptions\
    \ (e.g., \u201Ccode that connects language models to tools and state\u201D)."
- id: 1c61b03547e1
  severity: writing
  text: "Define every acronym on first use. Examples: LLM (large language model) in\
    \ the abstract, PEV (Plan\u2011Execute\u2011Verify) in Section\u202F3.2, and MAS\
    \ (multi\u2011agent system) in Section\u202F4."
- id: d86c25213af5
  severity: writing
  text: "Avoid overly dense noun\u2011clusters like \u201Ccode\u2011centric agent\
    \ systems where reasoning, action, state, feedback, and verification are organized\
    \ around executable, inspectable, and stateful programs\u201D. Rewrite as a series\
    \ of short sentences for readability."
- id: b38fc6726ebb
  severity: writing
  text: "Limit the use of domain\u2011specific jargon (e.g., \u201Csemantic conflict\
    \ resolution\u201D, \u201Ctransactional shared program state\u201D, \u201Cbelief\u2011\
    state divergence\u201D) unless the target audience is explicitly expert; provide\
    \ plain\u2011language equivalents or brief explanations."
- id: c3ae969746ed
  severity: writing
  text: Reduce the number of parenthetical citations that break the narrative flow.
    Group related works in a single sentence and move the citation list to the end
    of the paragraph.
artifact_hash: cbd4e8e17c331b3d11d6d3473a72ca30389ded91296199ea84247ea30361db9d
artifact_path: projects/PROJ-606-https-arxiv-org-abs-2605-18747/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-22T10:57:57.356071Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript presents a thorough survey of “code as agent harness” but frequently relies on dense jargon that can alienate readers outside the immediate research community. In the abstract and Introduction (Section 1) terms such as *operational substrate* and *agentic systems* are introduced without concrete definition, leaving the reader to infer meaning from context. A clearer phrasing would describe code as “the software layer that lets language models call tools, store state, and run tests”.

Throughout the paper, many acronyms appear without first‑time expansion. For instance, **PEV** (Plan‑Execute‑Verify) is only explained in Section 3.2, while **MAS** (multi‑agent system) appears in Section 4 without prior definition. Adding a brief definition at first occurrence would improve accessibility.

The taxonomy (Figure 1) and subsequent sections are littered with multi‑word compounds (“harness interface”, “harness mechanisms”, “harness engineering”) that repeat the word *harness* without adding semantic value. Re‑phrasing these as “code interface”, “supporting modules”, and “engineered infrastructure” would make the text more readable.

Several paragraphs contain long, nested noun phrases that obscure the main point. Example: “code‑centric agent systems where reasoning, action, state, feedback, and verification are organized around executable, inspectable, and stateful programs” (Section 2). Breaking this into two sentences—first stating what the system does, then listing the properties—helps comprehension.

Finally, the citation style often interleaves many references within a single sentence, which interrupts the narrative. Grouping related works (e.g., “Recent work on tool‑use [45–48] demonstrates …”) and moving the full list to the end of the paragraph would streamline reading.

Addressing these points will broaden the paper’s reach and make its valuable taxonomy more approachable for a wider audience.
