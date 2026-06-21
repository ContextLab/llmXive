---
action_items:
- id: 83ea223aeb9a
  severity: writing
  text: "Add a dedicated Data and Code Availability statement that includes explicit\
    \ URLs (with DOIs when possible) for the simulation dataset, the generated trajectory\
    \ files, and any code repositories (e.g., the Guava harness, data\u2011generation\
    \ engine, and training scripts)."
- id: c6e7d8176ed2
  severity: writing
  text: "Specify the licensing terms for all released assets (simulation trajectories,\
    \ model checkpoints, and source code). If the dataset is derived from RoboSuite,\
    \ cite RoboSuite\u2019s license and clarify whether any modifications are redistributed\
    \ under a compatible license."
- id: 73ee0c9d89e8
  severity: writing
  text: Provide a schema description for the trajectory files (e.g., JSON fields for
    observations, tool calls, reasoning traces, and success flags) and document how
    missing or corrupted entries are detected and filtered during preprocessing.
- id: 6566df316c47
  severity: writing
  text: Include version identifiers (e.g., Git commit hashes or release tags) for
    the codebase used to generate the data and train the 4B model, so that reviewers
    can reproduce the exact experimental setup.
- id: b852ddf8e488
  severity: writing
  text: "Verify that all external URLs (project page, image assets, referenced tool\
    \ implementations such as SAM3) are persistent; consider archiving them via Zenodo\
    \ or adding DOI references to mitigate link\u2011rot."
- id: 06602e6405e4
  severity: writing
  text: "Clarify the provenance of the 2K simulation trajectories: describe the random\
    \ seeds, scene randomization parameters, and any post\u2011processing steps that\
    \ could affect reproducibility."
- id: 5d773fe8aff3
  severity: writing
  text: "State the data\u2011handling policy for privacy or safety\u2011critical information\
    \ (e.g., real\u2011world RGB\u2011D recordings) and confirm that no personally\
    \ identifiable information is included."
artifact_hash: 305fa4e0caf5509b3ff951ed539855921f525d3dfdda7d54d245e51eb00f86f3
artifact_path: projects/PROJ-739-guava-an-effective-and-universal-harness/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T00:45:22.356771Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript focuses on a harness framework (Guava) for embodied manipulation and reports strong empirical results, but it lacks sufficient attention to data‑quality aspects that are essential for reproducibility and long‑term usability.

**Provenance & Licensing**  
The paper describes a “data generation engine” that collects ~2 K trajectories in RoboSuite, yet it does not disclose where these trajectories are stored, under what license, or how external users can obtain them. RoboSuite itself is open‑source, but the derived dataset may have additional restrictions; without an explicit statement, downstream users cannot be sure they are complying with the original license. The same issue applies to the released 4 B model checkpoint (Qwen3.5‑4B) and to the tool implementations (e.g., SAM3) that are invoked by the harness.

**Schema & Missing‑Data Handling**  
Section 6 (Appendix) mentions filtering steps (removing failed episodes, de‑duplicating, manual inspection) but provides no formal schema for the trajectory files. There is no description of the fields (e.g., timestamps, observation modalities, tool‑call JSON, success flag) nor of how missing observations (e.g., dropped RGB‑D frames) are represented and handled during training. This omission makes it difficult for others to parse the data correctly or to extend the pipeline.

**Version Control & Reproducibility**  
All experiments are said to run on “8 NVIDIA H100 80 GB GPUs” with specific hyper‑parameters, but the exact code version (Git commit, tag, or release) is not reported. Without such identifiers, reproducing the exact training pipeline (SFT + GRPO) is fragile, especially given the many moving parts (vision encoder freeze, optimizer settings, DeepSpeed ZeRO‑3 configuration).

**Link Rot & External Resources**  
The manuscript includes a project‑page URL (`https://guava-harness.github.io`) and numerous figure files embedded in the PDF. No archival copies (e.g., Zenodo snapshots) are provided, and no DOIs are attached to the external references. Over time these links may become unavailable, jeopardizing the paper’s long‑term accessibility.

**Recommendations**  
To bring the paper up to community standards for data quality, the authors should add a concise Data and Code Availability section that enumerates all released artifacts, their licenses, and persistent identifiers. A brief data‑card (similar to “Datasheets for Datasets”) describing the trajectory schema, random‑seed settings, and missing‑data policies would greatly aid reproducibility. Finally, archiving the project page and any large assets in a stable repository (Zenodo, Figshare) will protect against link rot.

Addressing these points will not alter the scientific claims but will substantially improve the paper’s transparency, reproducibility, and long‑term impact.
