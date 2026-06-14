---
action_items:
- id: ca45d2b15687
  severity: writing
  text: Specify data licenses for the RealOmin-Open Dataset and the generated Minecraft
    trajectories to ensure legal compliance and reproducibility.
- id: b3fb1da91c71
  severity: writing
  text: Add URLs to dataset citations in main.bib (e.g., genrobot2025opendata) to
    prevent link rot and enable verification.
- id: e3db51e9732c
  severity: science
  text: Document data preprocessing steps, specifically synchronization verification
    and missing-data handling, in the experiments section.
artifact_hash: 23197b85ae0bafaaddd0cb8ec8c0f5430ac77fd724ba8930f4eb33d7998307b0
artifact_path: projects/PROJ-641-https-arxiv-org-abs-2605-28816/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-14T07:48:10.831393Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on data quality, provenance, and reproducibility aspects of the manuscript.

**Data Provenance and Licensing**
The manuscript relies on two primary data sources: generated Minecraft trajectories (`sections/experiments.tex`, lines 30–35) and the RealOmin-Open Dataset (`sections/experiments.tex`, lines 130–135). While the action schemas are well-documented in `sections/appendix.tex` (Tables `tab:game-action-format`, `tab:robot-action-format`), the legal and usage terms for these datasets are absent. Specifically, no license is specified for the generated Minecraft data or the RealOmin dataset. Without explicit licensing information (e.g., Creative Commons, MIT, or proprietary restrictions), downstream users cannot determine permissible uses, which is a critical gap for reproducibility and legal compliance.

**Bibliography and Link Stability**
The bibliography (`main.bib`) contains entries for key datasets that lack persistent URLs. For instance, the entry `genrobot2025opendata` provides a title but no `url` or `howpublished` field containing a link. Similarly, the project page (`research.nvidia.com/labs/sil/projects/gamma-world`) is cited in the main text but not in the bibliography. To mitigate link rot and ensure long-term verifiability, all dataset citations should include stable URLs (e.g., GitHub repositories, Zenodo DOIs, or official hosting pages).

**Data Processing and Versioning**
The paper claims to construct "synchronized multi-agent Minecraft trajectories" but does not detail the synchronization methodology or how desynchronization was handled. There is no mention of missing-data handling (e.g., dropped frames, incomplete action traces) during preprocessing. Additionally, no version numbers are provided for the datasets or the data generation pipeline (inspired by `SolarisEngine`). For reproducibility, the authors should specify dataset versions, pipeline commit hashes, and describe quality control measures for data integrity.

**Recommendations**
To address these concerns, the authors should add a "Data Availability" section detailing licenses, URLs, and versions. The bibliography must be updated to include direct links to datasets. Finally, the experiments section should expand on data preprocessing, specifically addressing synchronization and missing-data protocols. These changes are necessary to ensure the data quality standards required for scientific reproducibility.
