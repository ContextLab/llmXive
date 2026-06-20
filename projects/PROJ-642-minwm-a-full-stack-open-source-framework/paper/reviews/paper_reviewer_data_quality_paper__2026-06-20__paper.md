---
action_items:
- id: d2f87edcbe59
  severity: writing
  text: "Add an explicit data\u2011license statement for all external datasets used\
    \ (SpatialVid, DL3DV, OpenVid, WorldPlay) and for the released code/checkpoints,\
    \ specifying the exact license (e.g., CC\u2011BY\u20114.0, MIT)."
- id: 0d265f6ff3ef
  severity: writing
  text: "Provide a concise data schema (e.g., JSON/YAML description) for the camera\u2011\
    annotated video files, including required fields (intrinsics, extrinsics, timestamps)\
    \ and how missing values are handled."
- id: 5b434e0eda15
  severity: writing
  text: "Document the version\u2011control provenance of the released repository (e.g.,\
    \ git commit hash, tag) and include a reproducible build script that pins all\
    \ dependencies."
- id: ef49349deba6
  severity: writing
  text: Add persistent, archived URLs (e.g., via Zenodo or Internet Archive) for all
    external resources cited (datasets, prior papers) to mitigate link rot, or include
    DOI links where available.
artifact_hash: 0ee056e55f4c06cb2eab61e5c44334fbdff8ec177adecd2d7f6251ef9b5e9f6a
artifact_path: projects/PROJ-642-minwm-a-full-stack-open-source-framework/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-20T04:33:48.227661Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript focuses on the technical pipeline of minWM but provides limited information on data‑quality aspects that are essential for reproducibility and long‑term usability.

**Provenance & Licensing**  
The paper mentions several external datasets (SpatialVid \cite{wang2025spatialvid}, DL3DV \cite{ling2024dl3dv}, OpenVid \cite{nan2024openvid}, WorldPlay \cite{sun2025worldplay}) but does not state their licenses or any permission to redistribute derived data. Without explicit licensing, downstream users cannot safely incorporate these resources into their own pipelines. The same issue applies to the released code and model checkpoints; the GitHub link is given, yet no license file or statement is referenced in the manuscript.

**Schema & Missing‑Data Handling**  
Section 3.1 describes camera parameters \(\{(K_i,T_i^{cw})\}\) and the PRoPE injection, but there is no formal schema for the video files (e.g., how intrinsics, extrinsics, and timestamps are stored, required file formats, or validation checks). Moreover, the paper does not discuss how missing or noisy pose estimates (especially for the SpatialVid experiments) are detected, filtered, or corrected, which is crucial given the observed failure modes.

**Version Control & Reproducibility**  
The authors claim to release “runnable scripts, checkpoints, documentation, and inference code,” yet the manuscript lacks any reference to a specific repository commit, tag, or release identifier. Providing a precise git SHA or a DOI for the released artifact would allow reviewers and future users to retrieve the exact version used in the experiments.

**Link Rot of External Sources**  
All external datasets are cited only by bibliography entries without persistent identifiers (DOI, arXiv URL, or archived link). If any of these resources become unavailable, the reproducibility of the ablations (Figures \ref{fig:ablation-data}, \ref{fig:ablation-steps}, \ref{fig:ablation-bs}) would be compromised. Including stable URLs or archiving the datasets in a long‑term repository would mitigate this risk.

**Recommendations**  
To bring the data‑quality documentation up to community standards, the authors should (1) add clear licensing information for every external dataset and for their own code/checkpoints, (2) provide a concise data schema and describe any preprocessing steps for handling missing or noisy camera poses, (3) reference a specific version of the GitHub repository (commit hash or release tag) and optionally a DOI, and (4) supply persistent URLs or archived copies for all cited external resources. Addressing these points will substantially improve the paper’s reproducibility and long‑term utility.
