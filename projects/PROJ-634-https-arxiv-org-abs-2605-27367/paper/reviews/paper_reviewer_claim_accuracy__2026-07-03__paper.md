---
action_items:
- id: 4def7cca6e38
  severity: writing
  text: The paper presents a comprehensive benchmark and a new model, but several
    factual claims regarding the scope of evaluation and the calculation of reported
    metrics are slightly overstated or ambiguous. First, the Introduction states the
    benchmark evaluates "41 models," while the text in Section 5.2 and the main results
    table (Table 1) clarify that there are "31 methods" with "41 variants." This distinction
    is important for reproducibility and accurate comparison; the claim should be
    refined to "4
artifact_hash: 306c5e78aff3c136de96c4c6956084c3af89239f10c2fba4682734d1809d3475
artifact_path: projects/PROJ-634-https-arxiv-org-abs-2605-27367/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T21:29:50.102812Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper presents a comprehensive benchmark and a new model, but several factual claims regarding the scope of evaluation and the calculation of reported metrics are slightly overstated or ambiguous.

First, the Introduction states the benchmark evaluates "41 models," while the text in Section 5.2 and the main results table (Table 1) clarify that there are "31 methods" with "41 variants." This distinction is important for reproducibility and accurate comparison; the claim should be refined to "41 model variants across 31 methods" to prevent the reader from assuming 41 distinct architectural approaches were tested.

Second, the claim that "full-context models OOM on dense inputs" is supported by the data, but the surrounding text in Section 5.2 implies a broader failure of feed-forward models. Table 1 shows that Fast3R (a feed-forward model) successfully runs on the Dense regime, whereas DA3-Giant (full-context) fails. The text should be precise: "Full-context attention models (e.g., DA3-Giant) OOM on dense inputs, while bounded-memory feed-forward models (e.g., Fast3R) remain scalable."

Third, the "Average" column in Table 1 for DA3-Giant reports an AbsRel of (0.183). The arithmetic mean of the reported non-OOM values (Single: 0.368, Sparse: 0.095, Medium: 0.086) is approximately 0.183. However, the table does not explicitly state that the average excludes the Dense regime (which is OOM). Without this clarification, a reader might assume the average includes a valid Dense score or that the calculation method is different. The table caption or footnote should explicitly state: "Average metrics are computed over non-OOM regimes only."

Finally, the dataset statistics in the Introduction ("22K scenes, 5.5M frames") are rounded approximations of the precise counts in Appendix E002 (21,810 scenes, ~5.5M frames). While minor, consistency in reporting (e.g., "approx. 22K scenes") would improve precision.

These issues are primarily matters of clarity and precise reporting rather than fundamental scientific errors, but they affect the reader's ability to trust the exact numbers presented.
