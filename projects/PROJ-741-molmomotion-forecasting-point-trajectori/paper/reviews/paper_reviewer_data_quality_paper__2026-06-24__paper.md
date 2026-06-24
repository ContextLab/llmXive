---
action_items:
- id: 772e91aa3330
  severity: writing
  text: "Add an explicit licensing statement for the MolmoMotion-1M dataset and the\
    \ PointMotionBench benchmark (e.g., CC\u2011BY, Apache 2.0) and include the same\
    \ license in the HuggingFace repository README."
- id: 57077c4423be
  severity: science
  text: Provide a clear provenance description for the source videos used in MolmoMotion-1M,
    including copyright status, any required permissions, and how copyrighted material
    is handled.
- id: bfd67d3bd8ac
  severity: writing
  text: Document the handling of missing or occluded points in the annotation pipeline
    (e.g., percentage of frames/points filtered, imputation strategy) and report these
    statistics in the paper or appendix.
- id: 85ed82fec44e
  severity: writing
  text: Introduce version identifiers (e.g., v1.0, git tags) for both the dataset
    releases and the codebase, and reference them in the manuscript to ensure reproducibility.
- id: 899b704b7e1e
  severity: writing
  text: Add persistent identifiers (DOIs or permanent URLs) for the external resources
    (HuggingFace collections, GitHub repo, technical website) to mitigate future link
    rot.
artifact_hash: 43d44b1b7f12aef158eaf0787875484ea72c6860cf8af3c796e4579ec99e55ab
artifact_path: projects/PROJ-741-molmomotion-forecasting-point-trajectori/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-24T15:40:51.561934Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript presents a compelling new task—goal‑conditioned 3D point motion forecasting—and a large‑scale data pipeline, but the data‑quality aspects need strengthening.

**Provenance & Licensing**  
The paper states that MolmoMotion-1M is built from “public video datasets” (EgoDex, HD‑EPIC, Xperience, etc.) but does not clarify the copyright status of those videos or whether redistribution is permitted. Moreover, the dataset and benchmark are hosted on HuggingFace without any explicit license declaration. For a reproducible research artifact, the authors must disclose the legal basis for re‑using the source videos (e.g., public domain, Creative Commons, or fair‑use justification) and attach a clear, permissive license to the released data and code.

**Schema & Missing‑Data Handling**  
The annotation pipeline (Sec. 3.2, Appendix A) describes several filtering steps (MAD outlier removal, depth‑ray smoothing, anchor‑track selection) but provides no quantitative summary of how many points or frames are discarded, nor how missing data (e.g., occluded points) are represented in the final dataset. Including statistics such as “average % of points retained per clip” and a description of any imputation or masking strategy would improve transparency and allow downstream users to assess data completeness.

**Version Control & Persistent Access**  
The paper links to a GitHub repository and HuggingFace collections, but does not reference any version tag, commit hash, or DOI. Without versioned releases, future users may encounter subtle changes that break reproducibility. Adding semantic version numbers (e.g., v1.0) and publishing a DOI (via Zenodo or similar) for both the code and the datasets would mitigate this risk.

**Link Rot & External Resources**  
All external URLs (GitHub, HuggingFace, technical website, blog) are currently functional, yet the manuscript does not provide fallback identifiers (e.g., arXiv DOI, permanent archive links). Including such identifiers ensures long‑term accessibility.

**Overall Assessment**  
The core scientific contributions are solid, but the data‑quality documentation is incomplete. Addressing the licensing, provenance, missing‑data reporting, versioning, and persistence concerns will bring the work up to the standards expected for open research artifacts.
