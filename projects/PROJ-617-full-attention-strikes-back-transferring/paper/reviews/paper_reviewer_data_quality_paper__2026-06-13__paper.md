---
action_items:
- id: a2679d630e4d
  severity: writing
  text: Add license information for FineWeb and Dolma 3 Longmimo Mix training datasets
    (Section 5.1, Appendix D.3)
- id: d671ac362bc4
  severity: writing
  text: Include version numbers for benchmark datasets (LongBench, RULER, MMLU-PRO)
    to ensure reproducibility
- id: 18f569aca9a0
  severity: writing
  text: Provide data card or datasheet link for the 8K-sample calibration sequence
    construction
- id: 0d35c8f706b5
  severity: writing
  text: Verify all external arXiv links (e.g., qwen3, fineweb) and add DOIs where
    available to mitigate link rot
artifact_hash: 2cdfc78b07a5bd64c78a8db6e3f4311cd8e2ebe3c52393699df0143a39308f60
artifact_path: projects/PROJ-617-full-attention-strikes-back-transferring/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-13T07:28:05.133374Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on data quality aspects of the manuscript. The paper makes substantial claims about training on FineWeb and Dolma 3 Longmimo Mix (Section 5.1, Appendix D.3), but lacks critical data provenance information.

**Data License & Provenance (Section 5.1, Appendix D.3):** Neither FineWeb nor Dolma 3 Longmimo Mix licenses are specified. FineWeb is a Common Crawl derivative with complex licensing implications; Dolma 3 has specific usage restrictions. This omission prevents downstream users from verifying compliance with dataset terms. The calibration sequence construction (Section 4.1) samples from FineWeb but provides no version identifier or filtering criteria beyond "documents with lengths between 32K and 80K tokens."

**Benchmark Versioning (Section 5.1):** LongBench, RULER, AIME24, AIME25, and MMLU-PRO are cited but no version numbers or commit hashes are provided. Benchmark datasets evolve; without version control, reproducibility is compromised. For example, RULER has multiple releases with different task configurations.

**External Link Stability:** Multiple arXiv citations (e.g., `qwen3`, `fineweb`, `olmo2026olmo3`) lack DOIs. These are prone to link rot. The bibliography includes several 2025-2026 dated entries that may be preprints subject to revision.

**Recommendation:** Add a data availability statement with dataset versions, licenses, and persistent identifiers. Consider including a data card for the custom calibration sequences. These additions would significantly improve reproducibility without requiring new experiments.
