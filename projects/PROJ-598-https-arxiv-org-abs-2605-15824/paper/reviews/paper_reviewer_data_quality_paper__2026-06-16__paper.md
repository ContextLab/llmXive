---
action_items:
- id: eaff53f6876b
  severity: science
  text: "Provide a public, version\u2011controlled release of the curated 62\u202F\
    K video\u2011garment triplet dataset (e.g., via Zenodo or a Git\u2011LFS repository)\
    \ and include a persistent DOI."
- id: 9c2af188b0cf
  severity: science
  text: "Specify the data license (e.g., CC\u2011BY\u20114.0) for the released dataset\
    \ and for any third\u2011party assets used (YOLOv8\u2011Seg, VLM prompts, etc.)."
- id: 69bab2f7e128
  severity: science
  text: "Add a detailed schema for the dataset (fields, formats, units, missing\u2011\
    value conventions) in the appendix or a separate data\u2011card."
- id: 719deb5d51f9
  severity: science
  text: Describe how missing or corrupt video frames, incomplete garment annotations,
    or failed OCR/VLM steps are detected and handled during curation.
- id: 540f138de284
  severity: writing
  text: Ensure all external URLs (e.g., the project page https://quanjiansong.github.io/projects/FashionChameleon/)
    are archived (e.g., via Internet Archive) and referenced with a stable identifier.
- id: 35e5c43fc35b
  severity: writing
  text: "Include a version\u2011control statement for the codebase (e.g., Git commit\
    \ hash) and for the model checkpoints used in experiments."
artifact_hash: 8ac732f80d31fee19845b13e35eb49deeae5414cb6cb993b15f1b25017de2aa1
artifact_path: projects/PROJ-598-https-arxiv-org-abs-2605-15824/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-16T04:08:32.800999Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript presents a compelling video‑generation system, but from a data‑quality perspective several critical gaps hinder reproducibility and long‑term usability.

1. **Dataset Availability & Provenance** – The “High‑Quality Data Curation Pipeline” (Appendix, Fig. \ref{fig:data_pipeline}) describes a four‑stage pipeline that yields ≈ 62 K triplets, yet there is no publicly accessible link, DOI, or version identifier for this dataset. Without an archive the dataset is effectively unavailable, and the provenance of the raw videos, garment images, and captions remains opaque.

2. **Licensing** – Neither the paper nor the supplementary material states the license under which the curated data are released, nor does it clarify the licensing of third‑party components (YOLOv8‑Seg, Gemini‑3.0 prompts, VLM tools). This omission raises legal ambiguities for downstream users and may impede open‑science sharing.

3. **Data Schema & Missing‑Data Handling** – The description of the dataset is limited to high‑level counts; there is no schema defining field names (e.g., “reference_image”, “garment_image”, “caption”), data types, resolution standards, or how missing entries (e.g., failed garment extraction) are recorded. The paper mentions “manual verification” but does not detail how incomplete or corrupted samples are filtered or annotated, which is essential for assessing data quality and bias.

4. **Version Control & Reproducibility** – The experimental section lists model checkpoints (e.g., WAN2.2‑5B‑TI2V) but does not provide a commit hash or release tag for the code that implements the KV‑cache rescheduling, streaming distillation, or the training scripts. A reproducibility statement with a GitHub URL and exact commit would allow independent verification.

5. **Link Rot & External Resources** – The only external URL is the project page (https://quanjiansong.github.io/projects/FashionChameleon/). This link is not archived, and no fallback is provided. Citing persistent identifiers (e.g., a Zenodo record) would mitigate future link rot.

6. **Documentation of Data Curation Steps** – While the pipeline stages are enumerated, the paper lacks quantitative reporting on filtering thresholds (e.g., optical‑flow magnitude cut‑offs, aesthetic scores) and the proportion of data discarded at each stage. Providing these statistics would enable readers to assess the rigor of the curation process.

Addressing these points—by releasing the dataset with a clear license, a detailed data‑card, and versioned code artifacts—will substantially improve the manuscript’s data quality, reproducibility, and long‑term impact.
