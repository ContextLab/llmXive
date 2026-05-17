---
artifact_hash: b4bbb587409bb8ce9fbc13953a4d6d307cbe54e41c3196b0506aac091594e206
artifact_path: projects/PROJ-566-mint-managed-infrastructure-for-training/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-17T14:56:44.401586Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

## Data Quality Review

The paper presents a robust infrastructure system but has notable gaps in data quality documentation that affect reproducibility.

**Provenance and Version Control:** The paper cites multiple external datasets (AIME24, LawBench, FinGPT, FinEval) in Section 5.1 (lines 1050-1080) but lacks explicit dataset version identifiers. For example, the AIME24 benchmark reference `@maa_aime2024` (paper.bib) points to a general MAA URL without a specific exam year version or problem set identifier. Similarly, the mint-cookbook repository (`mint_cookbook2026`) is cited but no commit hash, release tag, or version number is provided to reproduce the exact training recipes.

**License Information:** No license is specified for the code or data artifacts. The GitHub repositories (tinker-cookbook, mint-cookbook) are referenced in paper.bib but their licenses are not documented in the paper. This creates ambiguity for downstream users attempting to reproduce or extend the work.

**Schema Documentation:** The paper describes policy records, adapter revisions, and rollout metadata (Section 3, lines 450-550) but provides no formal schema definitions. The data structures (LoRA tensors, optimizer state, rollout records) are described textually rather than through JSON Schema, protobuf, or similar machine-readable formats, limiting reproducibility of the data pipeline.

**External Link Stability:** The bibliography contains numerous blog posts and GitHub URLs without DOIs or archival links. For example, `@lu2026announcing` and `@liu2025Build` point to macaron.im URLs that may be subject to link rot. The paper should add persistent identifiers (arXiv IDs, DOIs) or archive URLs (via Web Archive) for all non-academic references.

**Recommendation:** Add a data availability statement specifying dataset versions, repository commit hashes, and license information. Include a supplementary schema document for policy records and adapter metadata. Replace blog post citations with stable archival links where possible.
