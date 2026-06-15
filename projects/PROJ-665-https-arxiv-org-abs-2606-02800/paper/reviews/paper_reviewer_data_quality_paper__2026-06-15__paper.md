---
action_items:
- id: f98e7d5e1227
  severity: science
  text: Data provenance lacks version identifiers for external datasets (e.g., DROID,
    BEHAVIOR-1K, CARLA). Add dataset version numbers or commit hashes to enable reproducibility.
- id: 75d2dd59466b
  severity: writing
  text: OpenMDW-1.1 license restricts redistribution; clarify whether raw training
    data is available under this license or only processed/filtered versions.
- id: 54d312be6560
  severity: writing
  text: External URLs (HuggingFace, GitHub) lack archival snapshots; add DOI or archive.org
    references to prevent link rot.
- id: d8262269f5c2
  severity: science
  text: Data filtering statistics (4.23% deduplication, 78%/46% retention at thresholds)
    lack breakdown by modality; add per-modality filtering metrics.
- id: 274a349b7324
  severity: writing
  text: Synthetic dataset schemas (SDG-PhyxSim, SDG-RobotSim, etc.) lack formal schema
    versioning; add JSON Schema references or version tags.
artifact_hash: 868016604b8d9a3bb37ad3c74cf4a71a551a99c22f54a694c5fb583a974a744e
artifact_path: projects/PROJ-665-https-arxiv-org-abs-2606-02800/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-15T06:16:53.681776Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on data quality aspects: provenance, licensing, schema, missing-data handling, version control, and external link stability.

**License & Redistribution:** The paper states code, checkpoints, synthetic datasets, and benchmarks are released under "OpenMDW-1.1 License" (Abstract, Section 1). This proprietary license restricts commercial use and redistribution. Unlike MIT/Apache, this prevents third-party verification of training data composition. Clarify whether raw training data is accessible or only processed artifacts (Section 3, Data).

**Data Provenance:** External datasets (DROID, BEHAVIOR-1K, CARLA, AgiBot) are cited but lack version identifiers (e.g., commit hashes, release tags). For reproducibility, add dataset versions to Table 2 (Robotics Data Breakdown) and Section 3.3 (Temporal and Motion Data).

**Filtering Transparency:** Section 3.1 reports 4.23% deduplication and 78%/46% retention at AI-judge thresholds, but doesn't break these down by modality (image-text, video-text, text-only). Table 1 shows sample counts but no filtering rates per modality. Add per-modality filtering statistics to enable assessment of selection bias.

**Schema Documentation:** Appendix A describes JSON caption schemas (Image/Video) but provides no formal schema versioning or JSON Schema references. Without version tags, future users cannot validate compatibility with trained models.

**Link Stability:** Multiple external URLs are provided (github.com/nvidia/cosmos, huggingface.co/collections/nvidia/cosmos3, etc.) without archival snapshots. These are subject to link rot; add DOI or archive.org references per academic standards.

**Synthetic Data Versioning:** SDG datasets (SDG-PhyxSim, SDG-RobotSim, SDG-DriveSim, SDG-SynHuman, SDG-Warehouse) are described in Appendix E with statistics but no dataset version identifiers. Add version tags to Table E1 (SDG Overview) for reproducibility.

**Missing Data Handling:** The paper describes filtering pipelines but doesn't report what fraction of original data was discarded and why. For the 7.8B raw images → 767M processed images pipeline, report retention rates and failure modes.
