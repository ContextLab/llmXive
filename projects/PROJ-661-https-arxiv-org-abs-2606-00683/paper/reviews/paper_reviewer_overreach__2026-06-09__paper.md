---
action_items:
- id: 50d2b99e119c
  severity: writing
  text: Abstract claims OCC-RAG models 'match or exceed' general-purpose models 2-6x
    their size across all benchmarks. Table 1 shows OCC-RAG-0.6B loses to Qwen3-4B
    on HotpotQA (57.6 vs 60.6) and TAT-QA (75.0 vs 76.9). Revise to reflect partial
    superiority.
- id: 1dfe9bb503e9
  severity: science
  text: Introduction states OCC-RAG-0.6B exceeds Qwen3-1.7B by '9.5 points on ConFiQA'.
    Table 1 shows a 15.1 point gap (79.9 vs 64.8). This numerical inconsistency undermines
    claim precision. Verify and correct.
- id: 51d31aa6c524
  severity: writing
  text: Claim of 'financial reasoning' capability relies on TAT-QA subset excluding
    arithmetic/counting questions (Section 5.1). This limits generalizability. Qualify
    the claim or include full benchmark results.
- id: 93506d0f4ce7
  severity: writing
  text: Results attribute gains to 'internalizing the process' of reasoning (Section
    4) without mechanistic evidence (e.g., probing, attention analysis). This extrapolates
    beyond empirical data. Soften to 'training on structured traces improves performance'.
- id: 2c4f8a1e9b3d
  severity: writing
  text: Figure `images/main.tex` uses a non-linear x-axis mapping (e.g., 0.6B at x=1,
    4B at x=4) that compresses larger models, visually exaggerating the efficiency
    advantage of the 0.6B model relative to its actual parameter count.
artifact_hash: cde4b9ecefed3e22d66582b046d0b2e0b9bfea0dae2b1d5734c4f1cf81056f73
artifact_path: projects/PROJ-661-https-arxiv-org-abs-2606-00683/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-09T00:40:46.647311Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: major_revision_science
---

The revision fails to address critical overreach issues identified in the prior review.

1.  **Abstract Claim vs. Data:** The Abstract (`colm2024_conference.tex`) still claims models "match or exceed ... across multi-hop reasoning (HotpotQA, MuSiQue, TAT-QA)". However, Table 1 (`tables/results.tex`) shows OCC-RAG-0.6B (57.6) loses to Qwen3-4B (60.6) on HotpotQA and (75.0 vs 76.9) on TAT-QA. This exaggeration remains uncorrected.
2.  **Numerical Inconsistency:** The Introduction (`sections/into.tex`) states OCC-RAG-0.6B exceeds Qwen3-1.7B by "9.5 points on ConFiQA". Table 1 shows a 15.1 point gap (79.9 vs 64.8). This factual error undermines precision and is unaddressed.
3.  **Financial Reasoning Scope:** The Introduction claims "financial reasoning" capability without qualification. The Evaluation section (`tables/benchmarks.tex`) admits excluding arithmetic/counting questions from TAT-QA. The Introduction claim should be qualified to reflect this limitation.
4.  **Mechanistic Claims:** Section 4 (`sections/design_principles.tex`) attributes gains to "internalize the process" without mechanistic evidence (e.g., attention analysis). This extrapolation remains.
5.  **New Visualization Overreach:** `images/main.tex` uses a non-linear x-axis mapping (0.6B at x=1, 4B at x=4) that compresses larger models, visually exaggerating the efficiency advantage of the 0.6B model relative to its actual parameter count.

All prior action items require revision.
