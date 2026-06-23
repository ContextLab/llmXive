---
action_items:
- id: 9b20aa8c039b
  severity: fatal
  text: "Add a clear data availability and licensing statement for all external datasets\
    \ (AMASS, LAFAN1, MotionMillion, PHUMA) and the internal 2\u202FB\u2011frame corpus,\
    \ including URLs, version identifiers, and the specific licenses under which each\
    \ source can be redistributed."
- id: b8d5447735e1
  severity: writing
  text: "Provide a formal schema (e.g., JSON/YAML or protobuf definition) for the\
    \ motion data format used after retargeting (joint ordering, units, timestamp\
    \ resolution, missing\u2011value conventions)."
- id: a88bd7be041f
  severity: writing
  text: "Describe the missing\u2011data handling pipeline in detail: how filtered\
    \ or corrupted clips are detected, what criteria trigger removal, and whether\
    \ any imputation or augmentation is applied."
- id: efcc412e220a
  severity: writing
  text: "Document the provenance of the in\u2011house recordings (date of capture,\
    \ sensor setup, calibration procedures) and assign a persistent identifier (e.g.,\
    \ DOI or Zenodo record) to ensure reproducibility."
- id: af221487b533
  severity: writing
  text: Ensure that all external resource links (e.g., dataset URLs, code repositories)
    are stable; consider using archived URLs (via archive.org) or providing a `requirements.txt`/`environment.yml`
    that pins exact versions of any preprocessing scripts.
- id: db12d000c6a5
  severity: writing
  text: "Include a version\u2011control snapshot (e.g., git commit hash) of the data\
    \ processing scripts used for filtering, segmentation, and augmentation, and make\
    \ these scripts publicly accessible."
artifact_hash: 11a83a092083d485002512d3e56d130e02aef8501fdca7259786be2bc34086fd
artifact_path: projects/PROJ-658-humanoid-gpt-scaling-data-and-structure/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-23T13:00:08.386593Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The review focuses exclusively on data‑quality aspects of the manuscript.

**Provenance & Licensing**  
The paper aggregates several large‑scale motion corpora (AMASS, LAFAN1, Motion‑X++, PHUMA, MotionMillion) and an internal “in‑house” dataset, yet it provides no explicit statements about the licenses governing these sources. Without clear licensing information, downstream users cannot legally redistribute or reuse the 2 B‑frame corpus. The internal recordings lack any provenance metadata (capture dates, sensor configurations, calibration details), making reproducibility difficult.

**Schema & Missing‑Data Handling**  
The manuscript mentions “retargeting” motions to the Unitree‑G1 joint space and applying “time‑warping augmentation,” but it does not define a formal data schema (joint ordering, units, timestamp granularity, or how missing joint values are represented). The filtering pipeline is described qualitatively (“strict filtering, segmentation, and augmentation”) without quantitative criteria or a reproducible script. Consequently, it is unclear how corrupted or incomplete clips are identified and whether any imputation is performed.

**Version Control & Link Rot**  
All external datasets are referenced only by citation keys (e.g., \cite{amass19}) with no persistent URLs or version identifiers. This raises the risk of link rot, as dataset releases may change over time. Moreover, the code used for data curation, clustering (HME), and augmentation is not linked to a specific repository commit; the paper provides no git hash or archive reference, hindering exact replication of the preprocessing steps.

**Recommendations**  
To meet community standards for data transparency, the authors should (1) add a comprehensive data‑availability section that lists each source, its license, and a stable download link; (2) publish a machine‑readable schema for the retargeted motion format; (3) detail the missing‑data detection and handling procedures; (4) supply provenance metadata for the proprietary recordings; (5) archive all preprocessing scripts with a fixed version control identifier; and (6) consider providing a DOI‑registered snapshot of the assembled 2 B‑frame dataset (or a subset) for reproducibility.

Addressing these points will substantially improve the paper’s data quality and ensure that the impressive scaling results can be independently verified and safely reused.
