---
action_items:
- id: 5ec4e4328d6b
  severity: science
  text: "Add an explicit data\u2011availability and licensing statement for all external\
    \ resources (NSD fMRI data, FLUX.2, Gemma\u20113, Qwen3\u2011VL, COCO image pool).\
    \ Specify the exact version/release used and include a permissive license identifier\
    \ (e.g., CC\u2011BY\u20114.0, MIT)."
- id: cad2402ec48f
  severity: writing
  text: Provide a persistent, archived URL (e.g., via Zenodo or OSF) for the project
    page and any code repositories referenced. Include a DOI to guard against link
    rot.
- id: 65775c7dd386
  severity: writing
  text: Document the schema used for the generated stimulus sets (image files, metadata,
    verification labels) and describe how missing or failed generations are handled
    (e.g., filtering criteria, fallback procedures).
- id: 968e1a0db793
  severity: writing
  text: "Include version\u2011control information for the pipeline (git commit hash,\
    \ branch name) and for the large models (model card identifiers, checkpoint hashes).\
    \ This aids reproducibility and provenance tracking."
- id: 5194c2b22e93
  severity: writing
  text: "Clarify how the retrieved images from the NSD and COCO pools are stored,\
    \ whether any preprocessing (e.g., normalization) is applied, and provide checksums\
    \ for the final image\u2011fMRI pairs to detect corruption."
artifact_hash: 3e7821bc4196322444417ea380054aced908f7d581b2fd2f7cbee1140a5fd1b0
artifact_path: projects/PROJ-660-https-arxiv-org-abs-2605-23895/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-16T10:19:24.174703Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript introduces **BrainCause**, a pipeline that synthesizes and edits images, retrieves stimuli from public datasets, and predicts fMRI responses using a pre‑trained encoder. While the scientific approach is well‑described, the review of data‑quality aspects reveals several gaps.

**Provenance and Licensing** – The paper relies on multiple external resources: the Natural Scenes Dataset (NSD), COCO image pool, FLUX.2, Gemma‑3‑IT, Qwen3‑VL, and the image‑to‑fMRI encoder from Beliy 2024. None of these resources are accompanied by a clear licensing statement within the manuscript (see lines 140‑170 where the datasets and models are mentioned). Without explicit licensing information, readers cannot determine whether the data and model weights can be redistributed or reused, which limits reproducibility and may raise legal concerns.

**Schema and Metadata** – The stimulus generation process creates three image categories (positives, semantic negatives, counterfactuals) and associates each with predicted fMRI vectors. However, the paper does not provide a formal schema (e.g., JSON or CSV column definitions) describing how these pairs are stored, what metadata (prompt text, verification label, edit instruction) accompanies each image, or how missing or filtered images are logged. This omission makes it difficult for downstream users to validate or extend the dataset.

**Missing‑Data Handling** – The authors note that semantic‑negative generation sometimes fails (see § 6.4, Fig. S7), yet the manuscript lacks a systematic description of how such failures are handled (e.g., whether the corresponding voxels are excluded, whether fallback negatives are generated, or how the failure rate is reported). A reproducible pipeline should explicitly log and report these cases.

**Version Control and Reproducibility** – The codebase, model checkpoints, and generated stimuli are not linked to any version‑controlled repository. No commit hash, branch name, or release tag is provided, nor are the exact model versions (e.g., FLUX.2‑Klein‑4B checkpoint hash). This hampers exact replication of the results, especially given the rapid evolution of the underlying generative models.

**Link Rot and Persistence** – The only external link is the project page (`https://yuvalgol123.github.io/BrainCause/`). No archival copy (e.g., via Internet Archive or a DOI‑minted repository) is cited, so future readers may lose access. The same applies to the arXiv pre‑print URL, which is stable but could benefit from a DOI reference.

**Recommendations** – To bring the data practices up to community standards, the authors should (i) add a dedicated “Data & Code Availability” section with explicit licenses and version identifiers; (ii) deposit the generated stimulus sets and any processing scripts in a persistent repository (Zenodo/OSF) and provide checksums; (iii) describe the data schema and missing‑data handling policies; and (iv) archive all external URLs. Addressing these points will substantially improve the paper’s transparency, reproducibility, and long‑term usability.
