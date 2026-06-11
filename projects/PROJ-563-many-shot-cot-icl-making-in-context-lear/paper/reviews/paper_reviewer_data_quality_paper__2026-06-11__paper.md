---
action_items:
- id: 007f0bb6e8f1
  severity: writing
  text: Dataset citations lack version numbers and license information. Add explicit
    dataset versions and licenses for reproducibility.
- id: 374a9e137af4
  severity: writing
  text: 'No data availability statement: processed demonstration data and embedding
    vectors are not publicly accessible. Provide a data repository link or commit
    hash.'
- id: 80d0416fb053
  severity: writing
  text: Bibliography contains truncated entries and missing URLs. Complete all references
    with DOIs or stable URLs.
- id: 41c24675ae5d
  severity: writing
  text: Embedding models lack version/commit specification. Add exact model versions
    for reproducibility.
- id: 06f08f733011
  severity: writing
  text: Experimental seeds are mentioned but exact seed values are not documented.
    Provide seed values for full reproducibility.
artifact_hash: da80d19d18126d829231e022c90784234c941daee73db4750a219950884e0e6f
artifact_path: projects/PROJ-563-many-shot-cot-icl-making-in-context-lear/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-11T10:45:06.343026Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

**Data Quality Review**

This paper makes substantial claims about many-shot CoT-ICL behavior that depend heavily on the quality and reproducibility of the underlying data and experimental setup. From a data quality lens, several concerns emerge:

**Dataset Provenance & Licensing (Lines 250-270, Appendix)**
The paper uses multiple datasets (GSM8K, MATH, DetectiveQA, SuperGLUE, NLU, TREC, BANKING77) but provides incomplete citation information. For example, the NLU and TREC citations lack specific version numbers, release dates, or URLs. Dataset licenses are not mentioned at all. This makes it difficult for reviewers or future researchers to verify that they are using the same data versions, which could affect reproducibility.

**Data Schema & Format (Section 4.3, Appendix)**
While the paper describes demonstration formats (Question + CoT + Answer), there is no formal schema documentation for the datasets used. The prompt templates in Appendix are helpful but don't specify edge cases (e.g., how missing CoT rationales are handled, how special characters are escaped).

**Data Leakage Prevention (Appendix, DetectiveQA section)**
The paper correctly addresses data leakage by filtering test instances that share the same data source as training. However, this filtering criteria is only documented for DetectiveQA, not for other datasets where similar leakage could occur.

**Embedding Model Versioning (Appendix)**
The curvature analysis depends on Qwen3-Embedding-4B and bge-m3 embeddings, but neither model version nor commit hash is specified. Embedding models can change behavior across versions, affecting curvature calculations.

**Bibliography Integrity**
Several references are incomplete or truncated (e.g., zoneofproximity is cut off mid-sentence). Some arXiv citations lack stable URLs. This creates link rot risk and undermines reproducibility.

**Recommendation:** Minor revision to add complete dataset citations with versions/licenses, a data availability statement, embedding model version specifications, and complete all bibliography entries.
