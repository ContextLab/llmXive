---
action_items:
- id: 77ccb2f7de89
  severity: writing
  text: 'Data provenance is underspecified: paper states training follows BAGEL pipeline
    but does not list specific dataset names, sizes, or licensing terms. Add a Data
    Availability subsection with explicit dataset sources and licenses.'
- id: 83758f0a10bd
  severity: writing
  text: No dataset versioning information provided. External URLs (e.g., project page
    at yuqingwang1029.github.io/RepresentationForcing) risk link rot. Archive datasets/code
    in a persistent repository (e.g., Zenodo, Hugging Face) with DOIs.
- id: 5e4731040188
  severity: writing
  text: Many bibliography entries cite arXiv preprints from 2024-2026 without stable
    publication venues. Replace with published versions where available, or provide
    permanent archive links for reproducibility.
artifact_hash: 0bf0beeeed30c8d210e5c1e3aba1eedb5ce01456059a286e2a46cd55dbe05f56
artifact_path: projects/PROJ-648-representation-forcing-for-bottleneck-fr/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-07T08:22:44.647079Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on data quality aspects: provenance, licensing, schema, version control, and external link stability.

**Data Provenance (sections/experiments.tex, "Data" paragraph):** The paper states training follows the BAGEL data pipeline but does not enumerate specific dataset names, sizes, or sources. For reproducibility, the authors should provide a table listing each dataset component (text-only, VQA, text-image pairs), its source repository, and approximate volume (e.g., number of samples or tokens).

**Licensing (no explicit section):** There is no statement regarding data licensing for the training datasets. Given the commercial affiliations (ByteDance Seed), this is a significant gap. Authors should explicitly declare licenses for all training data components and clarify any restrictions on model redistribution.

**Version Control (no explicit section):** No dataset version numbers or commit hashes are provided. The project page URL (lines 109-110: \checkdata[Project Page]) is a GitHub Pages link that may suffer from link rot. Recommend archiving data/code releases with persistent identifiers (e.g., Zenodo DOI, Hugging Face dataset card).

**External Reference Stability (main.bib):** Many bibliography entries cite arXiv preprints from 2024-2026 (e.g., bagel: arXiv:2505.14683, dinov3: arXiv:2508.10104, jit: arXiv:2511.13720). Some dates appear future-dated relative to typical publication cycles. These should be replaced with published venue versions where available, or the arXiv URLs should be supplemented with DOIs.

**Schema/Structure:** No discussion of data schema, preprocessing pipelines, or filtering criteria beyond the vague "follow BAGEL pipeline" statement. This limits reproducibility for researchers attempting to replicate the training setup.

**Missing-Data Handling:** The paper does not address how missing or incomplete multimodal data (e.g., text-image pairs without aligned captions) was handled during preprocessing. This should be documented.

These are primarily writing-level fixes that do not require re-running experiments, but they are necessary for data reproducibility and compliance with standard data-quality expectations in ML research.
