---
action_items:
- id: fe04090270ba
  severity: writing
  text: Add explicit license declaration for EywaBench and cite source dataset licenses
    (e.g., MMLU-Pro, TabArena) in Section 'EywaBench Details' to ensure legal compliance
    and provenance.
- id: 2ee8cd712e2f
  severity: writing
  text: Fix truncated URLs in Figure 1 caption (e.g., 'https://en.wikipedia.org/wiki/Avatar_(2009_film')
    to prevent link rot and ensure referential integrity.
- id: ab41be9de7e7
  severity: science
  text: Clarify the 'label' column type in Table 1 (tab:eywabench_schema); it is defined
    as 'string' but time-series/numeric tasks require structured numeric labels for
    evaluation.
- id: a7ef05d20af3
  severity: writing
  text: Specify version tags or commit hashes for source datasets (DeepPrinciple,
    MMLU-Pro, fev-bench, TabArena) to enable exact benchmark reproducibility.
artifact_hash: 6f6f16bf33fe17a682df44afbf900ee0d80c1586f03954b67f158a9d54f94900
artifact_path: projects/PROJ-573-https-arxiv-org-abs-2604-27351/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-07T08:08:15.565203Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on data quality, provenance, schema, and external link integrity.

**Provenance and Licensing**
Section `sec:dataset_details` (e002, e003) describes the composition of *EywaBench* by aggregating four source datasets (DeepPrinciple, MMLU-Pro, fev-bench, TabArena). However, the manuscript lacks explicit licensing information for the new benchmark or the source datasets. Without a declared license (e.g., CC-BY, MIT), the usability and redistribution rights of the benchmark are unclear. Additionally, the specific versions of the source datasets are not cited (e.g., MMLU-Pro v1.0 vs. latest), which hampers reproducibility. Please add a license declaration and version identifiers in the appendix or Section 5.

**Schema Integrity**
Table `tab:eywabench_schema` (e002, e003) defines the `label` column type as `string`. Given that *EywaBench* includes time-series and tabular regression tasks (Section 5.1), labels for these instances are likely numeric or structured sequences. A schema that enforces `string` for all labels may cause type mismatches during evaluation or obscure the nature of the ground truth. The schema should reflect the actual data types used in the metrics (e.g., `float` for regression, `string` for classification).

**External Link Integrity**
The critical elements list indicates truncated URLs in the manuscript text, specifically in Figure 1 caption (e000): `https://en.wikipedia.org/wiki/Avatar_(2009_film`. This truncation suggests a LaTeX formatting error that may result in broken links in the compiled PDF. All external references, including GitHub repositories (`https://github.com/Violet24K/Eywa`), must be verified for validity and completeness to prevent link rot.

**Recommendation**
Address the licensing omission and schema definition to meet standard data publication requirements. Verify and fix all external URLs. These are minor revisions but critical for data quality and reproducibility.
