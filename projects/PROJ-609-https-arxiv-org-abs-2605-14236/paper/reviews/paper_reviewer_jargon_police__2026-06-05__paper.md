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
reviewed_at: '2026-06-05T07:39:51.603510Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

**Jargon Overuse Review**

This manuscript is technically sound but relies on field-specific acronyms and terminology that may exclude non-specialist readers in Information Retrieval (IR) or Applied Machine Learning. While many terms are standard for the target venue (ACL/EMNLP), the "jargon_police" lens requires strict adherence to defining terms at first use and preferring plain language where possible.

**1. Undefined Acronyms**
The Abstract introduces **NDCG@10** without expansion. While standard in IR, it is not universally known outside the field. It should be expanded to "Normalized Discounted Cumulative Gain at 10" on first use (Abstract, Paragraph 1). Similarly, **BEIR** is referenced in the Introduction ("BEIR-style tasks") without definition. The full name "Benchmarking Information Retrieval" should be provided. In Table 1's caption, **CI** is used for "Confidence Interval"; this should be spelled out to aid readers unfamiliar with statistical abbreviations.

**2. Technical Jargon**
The Abstract uses the phrase **"call-constrained regime"**. This is slightly opaque; "call-limited setting" or "budget-constrained scenario" is more accessible. **BM25** is used in Section 5 ("zero-cost BM25 prior") without definition. While a standard retrieval baseline, defining it briefly (e.g., "BM25 sparse retrieval prior") improves clarity. The term **"oracle"** is used frequently (e.g., "randomized-direction oracle"). While standard in algorithmic theory, a brief parenthetical clarification (e.g., "oracle (comparison mechanism)") in Section 3 would help general readers.

**3. Math Notation**
The paper uses **top-$K$** and **$NDCG@10$** extensively. Ensure these are introduced with text explanations before relying on the notation (e.g., "top-$K$ (the highest-ranked $K$ documents)").

**Recommendation**
Address these definitions in the Abstract and Introduction to ensure accessibility. Most changes are minor edits (adding parenthetical expansions) that do not affect the scientific claims but significantly improve readability for a broader audience.
