---
action_items:
- id: 989b58722b82
  severity: writing
  text: The manuscript relies heavily on specialized terminology that obscures meaning
    for non-expert readers. The most frequent offender is "structural affordances,"
    which appears in the Abstract, Introduction, and Related Work without ever being
    defined. While the authors imply it refers to schemas or query capabilities, a
    general reader cannot parse this without guessing. Similarly, "native execution
    engines" (Section 2.1) and "atomic-unit retrieval" (Section 5) are jargon-heavy
    phrases that could be
artifact_hash: 6b55048d0f0cf12263aa0420c5a331e1157aabe9768489e7c4eadd1c3653e932
artifact_path: projects/PROJ-644-omniretrieval-unified-retrieval-across-h/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T16:49:03.352733Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on specialized terminology that obscures meaning for non-expert readers. The most frequent offender is "structural affordances," which appears in the Abstract, Introduction, and Related Work without ever being defined. While the authors imply it refers to schemas or query capabilities, a general reader cannot parse this without guessing. Similarly, "native execution engines" (Section 2.1) and "atomic-unit retrieval" (Section 5) are jargon-heavy phrases that could be replaced with "databases," "query processors," or "single-source retrieval" respectively.

The term "verbalized" in Section 2.4 is used to describe converting structured results (rows, triples) into text, but this is not standard terminology outside of specific NLP sub-fields; "converted to text" or "summarized" would be clearer. Additionally, "backbone" is used repeatedly to refer to the underlying LLM (e.g., Section 3.1), which is acceptable in the field but should be explicitly defined as "base model" or "underlying LLM" upon first mention to aid broader comprehension.

Finally, "modality gap" (Section 1) is used to describe a bias in retrieval but lacks a concrete definition. The paper assumes the reader understands that this refers to the mismatch between query form and source structure. Replacing these terms with plainer language or adding brief parenthetical definitions would significantly improve accessibility without sacrificing precision.
