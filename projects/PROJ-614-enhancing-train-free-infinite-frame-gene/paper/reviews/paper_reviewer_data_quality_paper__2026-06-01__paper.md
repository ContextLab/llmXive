---
action_items:
- id: 7c02ab3093c4
  severity: writing
  text: The paper lacks explicit license information for VBench, NarrLV, and foundation
    models (VideoCrafter2, Wan2.1). Add a data availability statement specifying licenses
    for all external datasets and models used.
- id: b8b8f752539d
  severity: writing
  text: No version numbers are specified for VBench or NarrLV benchmarks. Include
    version identifiers or commit hashes to ensure reproducibility of evaluation results.
- id: 1645e314732f
  severity: writing
  text: The project page URL (https://xiaokunfeng.github.io/miga_homepage/) in the
    abstract has no archival guarantee. Consider adding an arXiv snapshot or DOI for
    permanent access.
- id: 68319942ac43
  severity: writing
  text: Evaluation data (VBench/NarrLV prompts, data splits) are not described with
    sufficient detail. Add a data card appendix specifying prompt counts, split sizes,
    and any preprocessing applied.
artifact_hash: 2fc45fd89cfd8c3cc27102ad20713af6a66d4f721af1c258a0cd318f7ea682b3
artifact_path: projects/PROJ-614-enhancing-train-free-infinite-frame-gene/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-01T11:03:41.591075Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on data quality aspects of the manuscript, including provenance, licensing, version control, and external resource sustainability.

**Data Provenance & Licensing (Section 4.1):** The paper cites VBench (huang2024vbench) and NarrLV (feng2025narrlv) as evaluation benchmarks, and uses VideoCrafter2 (chen2024videocrafter2) and Wan2.1 (wan2025wan) as foundation models. However, no explicit license information is provided for any of these resources. Given that some video generation models and benchmarks have restrictive licenses (e.g., research-only, non-commercial), this omission affects reproducibility and downstream use. Please add a dedicated "Data Availability and Licensing" subsection in the Appendix that specifies the license type for each external resource.

**Version Control (Section 4.1):** The benchmarks and models are cited but lack version specifications. VBench has undergone multiple updates since its initial release; without version numbers, readers cannot reproduce the exact evaluation setup. Similarly, Wan2.1-1.3B may have multiple checkpoints. Recommend adding version identifiers (e.g., "VBench v1.2", "Wan2.1 checkpoint sha256:...") or repository commit hashes in the implementation details appendix.

**Link Rot Risk:** The project page URL in the abstract (line 167: `https://xiaokunfeng.github.io/miga_homepage/`) is a potential link rot concern. Personal GitHub Pages may become inaccessible over time. Consider depositing supplementary materials in a permanent archive (e.g., Zenodo, arXiv supplementary) and citing the DOI.

**Missing Data Documentation:** The paper mentions using evaluation prompts with TNA counts of 2, 3, and 4 (Section 4.1), but does not specify the total number of prompts, whether they were sampled or exhaustively used, or any preprocessing applied. For reproducibility, add a data card in the appendix detailing: (1) total prompt counts per benchmark, (2) train/test split methodology, (3) any filtering or augmentation steps.

**Code/Data Availability Statement:** The paper does not explicitly state whether code, evaluation data, or model weights will be publicly released. Given the "train-free" nature of the method, releasing code is critical for verification. Please include a clear statement on data/code availability before submission.
