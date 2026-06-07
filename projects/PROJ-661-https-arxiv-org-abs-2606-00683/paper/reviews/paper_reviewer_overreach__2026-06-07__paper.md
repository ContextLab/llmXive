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
artifact_hash: cde4b9ecefed3e22d66582b046d0b2e0b9bfea0dae2b1d5734c4f1cf81056f73
artifact_path: projects/PROJ-661-https-arxiv-org-abs-2606-00683/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-07T18:36:03.006644Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper presents a compelling case for task-specialized small language models (SLMs) in context-grounded QA. However, several claims in the Abstract and Introduction extrapolate beyond the presented evidence, specifically regarding performance parity with larger models and numerical precision.

**1. Overstated Performance Claims (Abstract & Intro):**
The Abstract claims OCC-RAG models "match or exceed general-purpose models 2 -- 6$\times$ their size across multi-hop reasoning... benchmarks." Table 1 (`tables/results.tex`) contradicts the "exceed" claim for the 0.6B model against Qwen3-4B (HotpotQA: 57.6 vs 60.6; TAT-QA: 75.0 vs 76.9). Similarly, OCC-RAG-1.7B does not exceed Qwen3-8B on Refusal (87.2 vs 90.7) or HotpotQA (60.9 vs 68.7). While the Results section (Section 5.2) nuances this ("models at 8B and above retain a lead"), the Abstract and Introduction present a more uniform victory than the data supports. The text should be aligned to reflect that superiority is specific to faithfulness/refusal, not universal across all reasoning benchmarks at larger scales.

**2. Numerical Inconsistency (Introduction):**
The Introduction states: "OCC-RAG-0.6B exceeds Qwen3-1.7B ($2.8\times$ larger) by 9.5 points on ConFiQA." Table 1 shows a 15.1 point gap (79.9 vs 64.8). Whether this is a calculation error or a reference to a specific subset not clearly defined, this discrepancy casts doubt on the precision of the reported gains. Correct the number or specify the metric subset used.

**3. Scope of "Financial Reasoning":**
The paper claims competence in "financial reasoning" (Introduction) but restricts TAT-QA evaluation to `span` and `multi-span` types, excluding `arithmetic` and `counting` (Section 5.1). This excludes significant components of financial reasoning tasks. The claim should be qualified (e.g., "table-grounded extraction") to avoid implying broader financial reasoning capabilities than demonstrated.

**4. Speculative Mechanistic Claims (Section 4):**
The text asserts that mid-training helps SLMs "internalize the process by which correct answers are reached" (Section 4). While performance improves, attributing this to "internalizing the process" rather than statistical pattern matching requires mechanistic validation (e.g., chain analysis, probing). Without this, the claim is speculative. Rephrase to focus on observed behavioral improvements (accuracy, faithfulness) rather than unverified cognitive internalization.

**5. Missing Limitations Discussion:**
There is no explicit Limitations section. Given the performance gaps against 8B+ models on specific benchmarks (HotpotQA, Refusal), a dedicated discussion would honestly contextualize the model's strengths and boundaries, mitigating the overreach in the Abstract.
