---
action_items:
- id: b0fd4f9fcbc4
  severity: writing
  text: "The manuscript does not provide explicit licensing information for any of\
    \ the external datasets listed in Table\u202F1 (e.g., DFC\u202F2019, UrbanScene3D,\
    \ etc.). Add a clear license table indicating the permissive/restrictive nature\
    \ of each source and any required attribution."
- id: cb833343a17f
  severity: writing
  text: "There is no formal provenance record (e.g., acquisition dates, sensor IDs,\
    \ processing version) for the satellite, aerial, and urban imagery used in the\
    \ data pipeline (Sec\u202F2.1). Include a metadata schema and version\u2011controlled\
    \ manifest for each data source."
- id: 1e8fb43e2099
  severity: writing
  text: "The paper lacks a description of how missing or corrupted data (e.g., cloud\u2011\
    covered satellite tiles, incomplete LiDAR scans) are detected, filtered, or imputed\
    \ during the training tile generation stage (Sec\u202F2.3). Add a missing\u2011\
    data handling strategy and report the proportion of discarded samples."
- id: 964ea71862fa
  severity: writing
  text: "External URLs (e.g., the Google\u202FEarth coverage footnote, the official\
    \ project page) are cited without archiving (e.g., via DOI or archive.org). Provide\
    \ persistent identifiers or archived snapshots to mitigate link\u2011rot."
- id: 019b0026774b
  severity: writing
  text: "No checksum or integrity verification is reported for the billions of Gaussian\
    \ primitives generated and stored in the production pipeline (Sec\u202F4.1). Include\
    \ SHA\u2011256 checksums or similar for each data block and describe the version\u2011\
    control system used for dataset updates."
- id: a290c9221f8d
  severity: writing
  text: The dataset schema (e.g., fields for geographic bounding box, GSD, acquisition
    angle, weather conditions) is only implicit in the text. Publish a formal schema
    (JSON/YAML) and make it part of the supplementary material to ensure reproducibility.
- id: 902933e07a83
  severity: writing
  text: "It is unclear whether the training data complies with privacy or export regulations\
    \ (e.g., high\u2011resolution aerial imagery may be restricted in certain jurisdictions).\
    \ Add a compliance statement and, if necessary, a data\u2011access request procedure."
artifact_hash: 889d5a8e39acbdaa7baa4d1b8f93a551383f0dbc1ede3c36f50fc7a5e7bb8167
artifact_path: projects/PROJ-693-abot-earth-0-5-generative-3d-earth-model/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-17T06:18:36.395993Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The review focuses exclusively on data‑quality aspects of the manuscript.

**Provenance & Licensing (Sec 2.1, Table 1)**  
The authors list several public datasets (DFC 2019, UrbanScene3D, UrbanBIS, etc.) but provide no explicit licensing information. Without a clear license table it is impossible for readers to assess whether the data can be redistributed or used for commercial purposes. This omission also hampers reproducibility, as downstream users cannot know which sources require attribution or are subject to non‑commercial clauses.

**Metadata & Schema (Sec 2.2–2.4)**  
While the paper describes a “unified coordinate transformation and metadata standardization” step, the concrete schema is never shown. Critical fields such as acquisition timestamp, sensor model, off‑nadir angle, weather conditions, and processing version are only mentioned in prose. A formal schema (e.g., JSON‑LD or CSV header specification) should be published so that the dataset can be ingested by other pipelines without ambiguity.

**Missing‑Data Handling (Sec 2.3 & 2.4)**  
The pipeline generates training tiles by sliding a 200 m × 200 m window over reconstructed 3DGS scenes. However, the manuscript does not explain how tiles containing large voids (e.g., due to cloud cover or missing aerial passes) are identified or repaired. The “Tile‑Level 3DGS Reconstruction Assessment” mentions PSNR/SSIM thresholds but provides no quantitative report of how many tiles are discarded or how missing information is imputed. This leaves a gap in understanding data completeness and potential bias in the training set.

**Version Control & Integrity (Sec 4.1)**  
The production pipeline creates ~320 k inference blocks comprising 3.2 trillion Gaussian primitives. No mechanism for versioning these blocks is described, nor are checksums or hash manifests provided. In large‑scale distributed environments, reproducibility and error detection rely on such integrity checks. The absence of any reference to a version‑control system (e.g., DVC, Git‑LFS) raises concerns about dataset drift over time.

**Link Rot & Persistent Identifiers**  
The paper references external resources (Google Earth coverage footnote, the official project page URL) without archiving them. Over the lifespan of a research artifact, URLs can become inaccessible, undermining the reproducibility of claims that depend on those sources. Using DOIs, arXiv identifiers, or archived snapshots would mitigate this risk.

**Compliance & Ethical Considerations**  
High‑resolution aerial and satellite imagery can be subject to export controls or privacy regulations in certain countries. The manuscript makes no statement regarding compliance with such regulations, nor does it describe any data‑access request process for restricted datasets. Including a compliance declaration would strengthen the ethical standing of the work.

**Recommendations**  
To bring the dataset to a publishable standard, the authors should (1) add a detailed license matrix for every external source, (2) publish a formal metadata schema, (3) describe missing‑data detection and imputation procedures with quantitative statistics, (4) provide versioning and integrity verification information for the generated Gaussian primitives, (5) replace volatile URLs with persistent identifiers, and (6) include a compliance statement for any restricted data. Addressing these points will substantially improve the transparency, reproducibility, and long‑term usability of the data that underpins the ABot‑Earth system.
