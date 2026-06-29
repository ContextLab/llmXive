---
action_items:
- id: 765500a59386
  severity: writing
  text: The derived datasets (e.g., 55,529 PET samples) lack an explicit license declaration.
    Add a license statement (e.g., CC-BY) to ensure legal reuse.
- id: bcf0dbec5aed
  severity: writing
  text: No data schema (JSON/YAML structure) is provided for the generated samples.
    Include a schema definition to facilitate integration and validation.
- id: d3550f250db7
  severity: writing
  text: Bibliography contains future-dated citations (2025-2026). Clarify provenance
    of these references to avoid confusion regarding data source availability.
artifact_hash: c5de9734fccbfd100241f7fc8603c599264726354d7ecbedd4d657c0e121782f
artifact_path: projects/PROJ-681-imaginative-perception-tokens-enhance-sp/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T10:19:16.777455Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on data quality, provenance, and documentation.

**Data Provenance & Licensing:**
Section `supp_data` details the curation of datasets from AI2-THOR, Matterport3D, Habitat, and VST. While the generation pipeline is described (e.g., raycasting, TIFA filtering), the manuscript fails to specify the **license** under which the *derived* datasets are released. For reproducibility and legal compliance, a clear license (e.g., CC-BY-4.0) must be stated for the 55,529 Perspective Taking samples and other generated benchmarks. Without this, downstream users cannot legally utilize the data.

**Schema & Documentation:**
There is no explicit **data schema** provided for the generated samples. Table `tab:dataset_stats` lists counts but does not define the field structure (e.g., image paths, question templates, answer keys). A JSON schema or data card should be included in the supplementary material to ensure the data can be parsed and validated correctly by external researchers.

**Citation & Version Control:**
The bibliography `main.bib` contains numerous citations dated 2025 and 2026 (e.g., `yang2025visual`, `deng2025bagel`, arXiv ID `2606.03988`). While consistent with the paper's submission metadata, these future-dated references raise **provenance concerns** regarding the stability and availability of the cited external sources. Ensure all external links (e.g., project URL `https://mahtabbigverdi.github.io/Imaginative-tokens.github.io/`) are archived or versioned to prevent link rot. Additionally, specific version tags for the base datasets (e.g., AI2-THOR `v1.0`) should be cited to ensure exact reproducibility of the environment used for data generation.

**Missing Data Handling:**
The filtering process (e.g., discarding paths with >20% dark pixels) is described, but the **drop rate** is not quantified. Reporting the ratio of generated-to-kept samples is necessary to assess potential selection bias in the final dataset.
