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
reviewed_at: '2026-06-10T21:55:47.969027Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

**Jargon Overuse Review — Re-Review Assessment**

This re-review confirms that **none of the five prior action items** from my previous jargon_police review have been adequately addressed in the current revision. All five issues remain unresolved:

1. **NDCG@10** (id: f0bc9d0a3b70): Still appears without definition in Abstract (line 30: "improve NDCG@10 per call") and Introduction (lines 105, 112, 117). The metric should be expanded as "Normalized Discounted Cumulative Gain at 10 (NDCG@10)" on first use.

2. **BEIR** (id: d3d03eaf4912): Appears in Introduction (line 130: "Across BEIR-style tasks") without the full name "Benchmarking Information Retrieval" being stated.

3. **CI abbreviation** (id: 7e61a93ac78d): Table 1 caption (line 185) still reads "95% bootstrap CI half-width" instead of "Confidence Interval (CI)".

4. **BM25** (id: d2704c93ba64): Appears in Results Section (line 250: "top N=100 BM25 candidates") and Section 4 (line 215) without the Okapi BM25 definition.

5. **call-constrained regime** (id: 49283a0a0e81): Abstract (line 30) still uses "call-constrained regime" instead of the suggested "call-limited setting."

**New Issues Identified:**
- **RAG** (Introduction line 45): "Retrieval-Augmented Generation (RAG)" is not expanded at first mention.
- **TREC** (Results line 245): "TREC DL2019/2020" appears without the full conference name.

Given that all five prior items remain unaddressed, this requires minor_revision status. These are all writing-level fixes that do not require re-running experiments.
