---
action_items:
- id: f0bc9d0a3b70
  severity: writing
  text: Define NDCG@10 at first use in Abstract and Introduction. Currently appears
    as 'NDCG@10' without expansion.
- id: d3d03eaf4912
  severity: writing
  text: Define BEIR (Benchmarking Information Retrieval) when first mentioned in Introduction.
- id: 7e61a93ac78d
  severity: writing
  text: Expand 'CI' to 'Confidence Interval' in Table 1 caption.
- id: d2704c93ba64
  severity: writing
  text: Define BM25 (Okapi BM25) in Section 5 or Introduction.
- id: 49283a0a0e81
  severity: writing
  text: Replace 'call-constrained regime' with 'call-limited setting' in Abstract
    for clarity.
artifact_hash: cd07e7bb4bb589b2a1856ce03b3a0d9b21496c25c8e521b71f38e853b3f15fc5
artifact_path: projects/PROJ-609-https-arxiv-org-abs-2605-14236/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-10T16:31:04.306203Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

**Jargon Overuse Review — Re-Review Assessment**

This re-review confirms that none of the five prior action items from the previous jargon_police review have been addressed in the current revision. All original issues remain:

1. **NDCG@10** (lines 48, 53, 163): The metric appears in the Abstract and Introduction without definition. Non-specialist readers will not know this is "Normalized Discounted Cumulative Gain at rank 10."

2. **BEIR** (line 57): Appears as "BEIR-style tasks" without expansion. The acronym should be defined at first mention (Benchmarking Information Retrieval).

3. **CI** (line 163, Table 1 caption): "95% bootstrap CI half-width" still uses the unexpanded abbreviation. Should read "Confidence Interval."

4. **BM25** (lines 163, 197, 229): Used throughout without definition. First appearance should expand to "Okapi BM25" or at minimum "BM25 (a standard information retrieval scoring function)."

5. **call-constrained regime** (lines 50, 199): This phrase remains in the Abstract and Results section. The prior suggestion to use "call-limited setting" was not adopted.

No new jargon issues were introduced in this revision. However, the persistence of all five prior writing-class issues prevents acceptance. These are straightforward editorial fixes that would significantly improve accessibility for readers outside the information retrieval community.
