---
action_items:
- id: d8d7a3b4b27b
  severity: writing
  text: 'Section 3.1 (Sourcing Tasks) and Table 1 use ''pp'' (e.g., ''~30 pp'') without
    defining it as ''percentage points''. While common in economics/stats, an adjacent-field
    PhD in NLP/ML might momentarily confuse this with ''parts per'' or ''pages''.
    Define at first use: ''percentage points (pp)''.'
- id: 6f1ff300eaa1
  severity: writing
  text: Section 3.2 (Mixing Tasks) and Table 1 introduce 'Raw' and 'Normalized' columns
    without defining the normalization metric. The text mentions 'average z-score'
    in Section 3, but the table header does not explicitly link 'Normalized' to 'z-score',
    forcing the reader to cross-reference. Add '(z-score)' to the 'Normalized' column
    header or define it in the table caption.
- id: 5b0731d128f1
  severity: writing
  text: Section 3.5 (Teacher Model) and Table 5 reference 'GLM-4.7-AWQ' and 'GPT-5.3-Codex'.
    These specific versioned model names (especially the hypothetical/future '5.3'
    and '4.7') are used without a brief gloss of their architecture or origin (e.g.,
    'GLM-4.7-AWQ, a quantized variant of the GLM-4.7 model'). While model names are
    proper nouns, the specific versioning implies a specific capability set not obvious
    to an outsider.
- id: aa15984a4e2a
  severity: writing
  text: "Section 4.1 (Sourcing Tasks in RL) introduces the data source name '\texttt{pymethods2test}'\
    \ without explaining the transformation. The text says it is 'competitive programming\
    \ recast as contracts', but the name itself is opaque. Add a brief parenthetical\
    \ on first use: '\texttt{pymethods2test} (a dataset converting competitive programming\
    \ problems into function-level contract verification tasks)'."
- id: bb5f6dcb9185
  severity: writing
  text: Section 3.6 (Filtering Agent Rollouts) and Appendix A.3 use the term 'turns'
    (e.g., 'fewer than 5 turns') without explicitly defining it as 'agent-environment
    interaction steps' or 'model response cycles'. In multi-turn dialogue, 'turn'
    is standard, but in agentic loops involving tool use, it can be ambiguous (does
    a tool call count as a turn?). Define 'turn' as 'one complete cycle of model generation
    and tool execution' at first use.
artifact_hash: 1762f575d6ad502232c74311f4c0e12a6d2ed21a38bf5e7d1493821d45367039
artifact_path: projects/PROJ-780-openthoughts-agent-data-recipes-for-agen/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-04T02:26:10.732260Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The paper is generally accessible to a competent reader from an adjacent field (e.g., an NLP researcher familiar with LLMs but not specifically with agentic RL pipelines). Most core concepts like SFT, RL, and standard benchmarks (SWE-Bench) are used correctly and are within the expected vocabulary of the discipline. However, there are several instances of in-group shorthand and undefined abbreviations that create minor friction for a reader not deeply embedded in this specific subfield's current jargon.

Specifically, the use of "pp" for percentage points is a common statistical shorthand that should be expanded at first use to avoid ambiguity with other "parts per" metrics. The "Normalized" column in the ablation tables relies on a "z-score" definition mentioned in the text but not explicitly linked in the table headers, requiring the reader to hunt for the definition. Additionally, specific data source names like `\texttt{pymethods2test}` and model version strings like `GLM-4.7-AWQ` are used without brief operational glosses, assuming the reader knows the specific transformation or architecture implied by these names. Finally, the term "turns" in the context of agent rollouts could be clarified to distinguish between dialogue turns and tool-execution cycles.

These are minor barriers that can be resolved with simple parenthetical expansions or table caption clarifications, ensuring the paper is self-contained for the target audience.
