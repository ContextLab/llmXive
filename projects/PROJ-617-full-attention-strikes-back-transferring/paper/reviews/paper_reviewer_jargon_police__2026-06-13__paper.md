---
action_items:
- id: d04f8a5b2a75
  severity: writing
  text: Define 'KV cache' as 'Key-Value cache' at first use in Abstract and Introduction.
- id: 3db07526d5ad
  severity: writing
  text: Expand 'RoPE' to 'Rotary Positional Embeddings' before first use in Section
    2.2.
- id: 3adceb5ab7e6
  severity: writing
  text: Define 'MQA' and 'GQA' (Multi-Query/Grouped-Query Attention) in Section 4.2.
- id: 6103099f4cf2
  severity: writing
  text: Define 'NIAH' as 'Needle-In-A-Haystack' before use in Figure captions and
    Tables.
- id: 78b7aecae631
  severity: writing
  text: Replace 'SOTA' macro with 'state-of-the-art' text in tables for clarity.
- id: f31328d76bb2
  severity: writing
  text: Clarify 'attention sinks' in Section 4.1 or cite the specific mechanism briefly.
artifact_hash: 2cdfc78b07a5bd64c78a8db6e3f4311cd8e2ebe3c52393699df0143a39308f60
artifact_path: projects/PROJ-617-full-attention-strikes-back-transferring/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-13T07:32:10.467855Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on jargon density and acronym usage, aiming to improve accessibility for non-specialist readers.

**Undefined Acronyms**
Several acronyms are used without definition at their first occurrence, creating barriers for readers outside the immediate subfield:
1.  **KV cache** (Abstract, Line 11; Introduction, Line 24): Should be expanded to "Key-Value cache" on first mention.
2.  **RoPE** (Section 2.2, Line 5): Appears without expansion. Define as "Rotary Positional Embeddings" before Equation 1.
3.  **MQA / GQA** (Section 4.2, Line 22): "Multi-Query Attention" and "Grouped-Query Attention" must be spelled out.
4.  **NIAH** (Figure 1b caption; Table 5): "Needle-In-A-Haystack" is a specific benchmark term that requires definition.
5.  **SOTA** (Table 1, Table 3, Table 4): The macro `\SOTA{}` renders "SOTA" visually. Replace with "state-of-the-art" text for plain-language compliance.

**Technical Jargon Density**
Certain phrases assume deep familiarity with hardware or specific training paradigms:
1.  **"native sparse training"** (Abstract, Line 19): "Native" is ambiguous. Consider "end-to-end sparse pretraining" for clarity.
2.  **"attention sinks"** (Section 4.1, Line 12): Referencing *streamingLLM* is good, but a brief parenthetical explanation (e.g., "tokens that accumulate attention mass") aids understanding.
3.  **"log-sum-exp pair"** (Section 4.4, Line 10): While standard in systems papers, "maximum and log-sum statistics" is more descriptive.
4.  **"half2 instructions"** (Section 4.4, Line 23): Highly specific CUDA terminology. Consider "vectorized half-precision loads" for broader readability.

**Recommendations**
Please address these expansions and simplifications to ensure the paper is accessible to a broader ML audience beyond sparse attention specialists.
