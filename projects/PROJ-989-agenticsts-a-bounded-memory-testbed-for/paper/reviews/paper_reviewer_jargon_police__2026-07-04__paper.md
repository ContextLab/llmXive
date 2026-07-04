---
action_items:
- id: 18c9dcf4850d
  severity: writing
  text: "Section 4.1, Eq. 1: The symbol `\u03C0` is used as the composition operator\
    \ without definition. While `\u03C0` is standard for policies, here it denotes\
    \ a prompt assembly function. Define it explicitly: 'where \u03C0 is the prompt\
    \ composition function that concatenates...'"
- id: 8ca55f9c79f7
  severity: writing
  text: 'Section 4.2: The terms ''operator prompts'' (L1), ''state-typed prompts''
    (L2), and ''game knowledge'' (L3) are introduced as proper nouns for specific
    layers. While the context implies their function, a brief parenthetical gloss
    at first use (e.g., ''L1 operator prompts (immutable role templates)'') would
    aid an adjacent-field reader.'
- id: 2bd3c457dbd2
  severity: writing
  text: 'Section 4.3: The routing tiers ''fast'', ''strategic'', ''analysis'', and
    ''evolution'' are used as specific technical categories. Define the criteria for
    each tier (e.g., ''fast: trivial combat plans; strategic: ordinary decisions'')
    in the first sentence of the paragraph to clarify the distinction for non-specialists.'
- id: a498c7091b27
  severity: writing
  text: 'Section 5.1: The condition names ''mode-a'', ''mode-b-frozen'', and ''full-frozen''
    are used as specific experimental labels. While defined in the text, they appear
    as code-like identifiers. Ensure the first mention of each includes a brief operational
    description (e.g., ''mode-a (human-authored L5 seed bodies)'') to prevent confusion
    with generic modes.'
- id: 17571848d226
  severity: writing
  text: 'Section 7: The term ''MCP'' is used in ''STS2MCP'' and ''MCP server'' without
    expansion. While likely ''Model Context Protocol'' in this ecosystem, it is not
    a universal standard. Define the acronym at first use in Section 7 or the Introduction.'
artifact_hash: 199901d5e4144b007deca7b5b20bcc2b010b84ade5616f6bb7430db503358c9f
artifact_path: projects/PROJ-989-agenticsts-a-bounded-memory-testbed-for/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-04T21:53:51.786988Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The paper is generally well-structured and avoids the worst excesses of in-group shorthand, successfully defining its core "bounded contract" concept early on. However, a competent reader from an adjacent field (e.g., a researcher in standard RL or NLP) would likely stumble on a few specific instances of undefined notation and in-group naming conventions.

First, in Section 4.1 (Equation 1), the symbol `π` is introduced as the composition operator. In the broader ML literature, `π` almost exclusively denotes a policy function. Here, it is repurposed as a prompt assembly function. While the context makes the intent clear, the lack of an explicit definition ("where π is the composition function...") forces the reader to infer the meaning, which is a minor barrier.

Second, the paper relies heavily on specific, code-like labels for its experimental conditions and architectural layers (e.g., "mode-a", "mode-b-frozen", "operator prompts", "state-typed prompts"). While these are defined in the text, they are presented as proper nouns without immediate operational glosses. For a reader outside this specific subfield, distinguishing "mode-a" from "mode-b" requires careful back-and-forth reading. A brief parenthetical explanation at the first mention of each (e.g., "mode-a (human-authored L5 seed bodies)") would significantly improve flow and accessibility.

Finally, the term "MCP" appears in Section 7 (referencing STS2MCP and MCP servers) without expansion. Given that "Model Context Protocol" is a specific, emerging standard in the agentic tooling space but not yet universal knowledge across all of AI, it should be spelled out at first use to ensure the reader understands the technical dependency.

These are minor friction points that can be resolved with simple parenthetical expansions, but they currently represent the primary jargon-related barriers to a smooth read for an adjacent-field expert.
