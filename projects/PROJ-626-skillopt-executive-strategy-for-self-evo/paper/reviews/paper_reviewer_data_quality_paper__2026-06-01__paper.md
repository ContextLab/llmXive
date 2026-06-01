---
action_items:
- id: f9ebd8597420
  severity: writing
  text: Add specific dataset version numbers or commit hashes for all benchmarks (e.g.,
    SearchQA, SpreadsheetBench) in references.bib or Section 4 to ensure data provenance
    reproducibility.
- id: 605fa7eafd2c
  severity: writing
  text: Specify an open-source license (e.g., MIT, Apache 2.0) for the released code
    and skill artifacts in sections/0_abstract.tex or the repository README.
- id: 3a6a6e384017
  severity: writing
  text: Provide a pinned Git commit hash or tag for the code at https://aka.ms/SkillOpt
    to prevent link rot and version drift between paper submission and code access.
artifact_hash: 50b35337a8a43777b79c281c4b9b1469c17e33c9dc40d15b61bd05b1b7b347e8
artifact_path: projects/PROJ-626-skillopt-executive-strategy-for-self-evo/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-01T00:50:14.433737Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

This review focuses on data quality, provenance, and reproducibility metadata within the manuscript.

**Data Provenance and Versioning:**
The paper relies on multiple external benchmarks (SearchQA, SpreadsheetBench, OfficeQA, etc.) described in `sections/4_experiments.tex` and cited in `references.bib`. While the text mentions `split_seed=42` for deterministic splits, it lacks specific dataset version identifiers (e.g., commit hashes, release tags, or dataset card versions). Without these, it is impossible to verify that the training/evaluation data matches the reported results, especially for datasets that may evolve over time (e.g., `li2026skillsbench` in `references.bib`).

**Artifact Licensing and Availability:**
The abstract (`sections/0_abstract.tex`) provides a code link (`https://aka.ms/SkillOpt`) but does not specify a software license for the released code or the generated skill artifacts (`best_skill.md`). This ambiguity prevents downstream users from understanding usage rights. Additionally, the bibliography contains several arXiv preprints and proprietary model references (`openai2026gpt54`) without API version constraints, limiting reproducibility of the optimization phase.

**Link Stability and Schema:**
The use of a Microsoft alias (`aka.ms`) for the code repository introduces a risk of link rot if the organization changes ownership. A permanent URL (e.g., Zenodo DOI or GitHub commit) would be more robust. Furthermore, while the paper describes the skill schema (`best_skill.md`, `edit_apply_report.json`), there is no formal schema definition (e.g., JSON Schema) provided for the benchmark inputs/outputs or the skill edit operations, which hinders automated validation of the data pipeline.

**Missing Data Handling:**
Section 4 notes that unmeasured cells are marked as `\na`, which is appropriate for result tables. However, the manuscript does not explicitly state how missing or failed benchmark executions (e.g., tool call timeouts) are handled during the rollout phase in `sections/3_methods.tex`. Clarifying whether these are excluded, imputed, or treated as zero-score failures is necessary for data integrity.

To reach `accept`, the authors must address the provenance, licensing, and version control gaps identified above.
