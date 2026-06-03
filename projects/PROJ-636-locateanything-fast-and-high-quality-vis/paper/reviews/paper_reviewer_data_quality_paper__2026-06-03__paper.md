---
action_items:
- id: f42df2cb017e
  severity: science
  text: Explicitly state the license for LocateAnything-Data in the main text or supplementary,
    given the aggregation of diverse source datasets (e.g., Unsplash, OpenImages)
    and synthetic generation via Qwen3-VL.
- id: 15cff7cc08e6
  severity: writing
  text: Correct the GitHub link in main.tex (currently points to 'Eagle/Embodied')
    to accurately reflect the LocateAnything code/data repository, or provide a direct
    dataset download link.
- id: 48c3f4514621
  severity: science
  text: Provide a version identifier or hash for the 138M-sample LocateAnything-Data
    to ensure reproducibility and data provenance tracking.
- id: 1eea0a24403a
  severity: writing
  text: Document the raw dataset schema (e.g., JSON/Parquet structure) for LocateAnything-Data
    in the supplementary, distinct from the model token schema described in sec/3_0_method.tex.
artifact_hash: fd5c6b9375343e0bf1127bc6f967de79045e8b07b55446fb41fe382f0df7e34c
artifact_path: projects/PROJ-636-locateanything-fast-and-high-quality-vis/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-03T13:48:29.260107Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

## Data Quality Review

This review evaluates the data provenance, licensing, schema, and availability aspects of the LocateAnything paper. While the methodological contribution is clear, the data documentation requires significant improvement to meet reproducibility standards for large-scale dataset papers.

**1. Data Licensing and Provenance (Critical)**
In `supp/data.tex` and `sec/3_0_method.tex`, the authors describe curating **LocateAnything-Data** from diverse sources (OpenImages, Objects365, Unsplash, SA-1B, GroundCUA, etc.) and synthesizing queries using Qwen3-VL and Molmo. However, the paper does not state the **license** for the resulting aggregated dataset. Aggregating datasets with different licenses (e.g., CC0, CC BY-NC-SA) and adding synthetic data derived from proprietary or licensed models creates complex derivative work obligations. Without a clear license statement (e.g., in `main.tex` or `supp/data.tex`), it is unclear if the dataset can be legally redistributed or used for further research. This is a significant barrier to adoption and reproducibility.

**2. Data Availability and Link Rot**
The `main.tex` file (Lines 12-16) provides a GitHub link: `\href{https://github.com/NVlabs/Eagle/tree/main/Embodied}{GitHub}`. This points to the "Eagle" repository, not "LocateAnything." While `chen2025eagle` is cited, the link ambiguity risks **link rot** or confusion regarding where the code and data reside. Furthermore, there is no direct link to download the 138M-sample dataset itself, only the model weights (`huggingface.co/nvidia/LocateAnything-3B`). For a paper claiming a "large-scale dataset" as a key contribution, a direct download path or clear instruction on accessing the data is required.

**3. Version Control and Schema**
The paper describes the *model token schema* (blocks, padding, coordinates) in `sec/3_0_method.tex` but does not document the **raw dataset schema** (e.g., how images and queries are stored in the 138M sample set). Additionally, no **version identifier** or content hash is provided for the dataset. Given the dynamic nature of synthetic data generation (using Qwen3-VL), the exact state of the data must be versioned to ensure that future evaluations match the reported results.

**4. Missing Data Handling**
`supp/data.tex` mentions constructing negative samples and filtering inconsistent predictions. However, there is no documentation on how missing annotations in the *source* datasets were handled prior to aggregation. A data quality report detailing missingness rates or imputation strategies would strengthen the provenance claims.

To proceed, the authors must clarify the licensing, correct the repository links, and provide dataset versioning information.
