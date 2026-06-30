---
action_items:
- id: e2e84099f276
  severity: science
  text: The paper cites multiple external datasets (SpatialVID, RealEstate10K, Sekai,
    DL3DV) and tools (MegaSaM) but fails to provide specific version numbers, commit
    hashes, or download dates. Without this, the data provenance is non-reproducible.
- id: 08c4d7abf482
  severity: writing
  text: The license for the combined training dataset is undefined. While some sources
    (e.g., RealEstate10K) have known licenses, the paper does not state the license
    governing the final curated mix or the synthetic UE5 data, creating legal ambiguity
    for downstream use.
- id: bddbfbb23194
  severity: science
  text: The paper claims to use 'action-rich gameplay recordings' and 'Sekai-Game'
    data but does not specify the schema for the action vectors (e.g., discrete vs.
    continuous, normalization range) or the exact coordinate system used for camera
    poses across the three data sources (UE, Real-world, Game).
- id: 4cee9acd3e13
  severity: writing
  text: External links to the project page and GitHub are provided in the metadata,
    but the paper does not include a 'Data Availability' section detailing the specific
    paths to the processed dataset, the cleaning scripts, or the version control strategy
    for the data pipeline.
artifact_hash: dd358f57d42e68a3445f4b34d5b2202a60d20e2d68878dcf007801dde467660f
artifact_path: projects/PROJ-717-dreamx-world-1-0-a-general-purpose-inter/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T05:20:20.945104Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript presents a sophisticated data pipeline for the DreamX-World model, combining synthetic (Unreal Engine), game, and real-world sources. However, from a strict data quality and reproducibility perspective, several critical gaps exist in the documentation of data provenance, schema, and licensing.

First, **provenance and versioning** are insufficiently detailed. In Section 2.1.2 ("Real-world and Game Data"), the authors cite datasets such as SpatialVID, RealEstate10K, Sekai, and DL3DV, and tools like MegaSaM. However, no version numbers, release dates, or specific commit hashes are provided for these external resources. Given that datasets like RealEstate10K or Sekai may have undergone updates or that MegaSaM's pose estimation performance varies by version, the inability to pin down the exact data state makes the experiment non-reproducible. The paper should explicitly list the versions of all external datasets and tools used.

Second, the **license and usage rights** for the final training corpus are not addressed. While the paper mentions combining data from various sources, it does not specify the license governing the resulting mixed dataset. For instance, if the synthetic UE5 data is proprietary or if the real-world data has restrictive licenses (e.g., CC-BY-NC), the "general-purpose" claim in the title is legally unsupported without a clear statement on the permissibility of redistribution or commercial use of the trained model and its training data. A dedicated "Data License" subsection is required.

Third, the **data schema and normalization** details are vague. Section 2.1.1 describes the UE data schema (WASD/IJKL actions, Euler angles), and Section 2.1.2 mentions converting game and real-world poses to a "common camera coordinate system." However, the specific transformation matrices, the definition of the coordinate system (e.g., OpenGL vs. DirectX conventions, axis orientation), and the normalization ranges for the action vectors are not provided. This lack of schema definition hinders the ability of other researchers to validate the geometric consistency claims or to integrate their own data into the pipeline.

Finally, while the paper provides links to a GitHub repository and project page, it lacks a formal **Data Availability Statement** detailing the location of the processed dataset, the cleaning scripts, and the version control history of the data pipeline. Without access to the specific cleaning scripts mentioned in Section 2.2 (e.g., the CLIP-based filtering logic or the SLERP interpolation parameters), the quality control process remains a "black box."

To address these issues, the authors should add a comprehensive data appendix or section that includes: (1) a table of all data sources with specific versions and licenses; (2) a detailed schema definition for the unified data format; (3) the exact coordinate system conventions and transformation logic; and (4) links to the specific versions of the data processing code and the final dataset (or instructions for its reconstruction).
