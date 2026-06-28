---
action_items:
- id: 00dfe0aa002d
  severity: writing
  text: Explicitly state the license of the Claw-SWE-Bench artifact (e.g., MIT) in
    Appendix I, not just upstream licenses.
- id: 9a2d9966df38
  severity: writing
  text: Add a version tag or commit hash for the code/data release to ensure reproducibility
    and prevent link rot.
- id: 1653b1012d40
  severity: writing
  text: Document the schema of the benchmark instances (JSON fields) or reference
    the exact SWE-bench schema version used.
- id: 0c3ad5a87a73
  severity: writing
  text: Reference the specific script or method used for 'Future-commit history is
    removed' cleaning step in Section 2.3.
artifact_hash: d91d9216ec1b23d5ae21a0d631e31b9f94ceb55943984c394279379a22a67899
artifact_path: projects/PROJ-695-claw-swe-bench-a-benchmark-for-evaluatin/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-28T17:56:37.410721Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The paper demonstrates strong provenance tracking for upstream datasets (SWE-bench Multilingual, Verified-Mini) in Section 2.1 and Appendix I. However, several data quality artifacts are missing or ambiguous, hindering full reproducibility and legal clarity.

First, the license of the *Claw-SWE-Bench* artifact itself is not explicitly declared. Appendix I details upstream licenses (MIT, BSD, GPL) and mentions a `REPO_LICENSES.md` file, but it does not state the license governing the new benchmark instances or the adapter code. Users need to know if they can redistribute the benchmark (e.g., "Claw-SWE-Bench is released under MIT").

Second, versioning is absent. The Abstract and Section 2 provide GitHub (`opensquilla/claw-swe-bench`) and Hugging Face (`TokenRhythm/Claw-SWE-Bench`) links, but no commit hash, tag, or version number (e.g., v1.0). Without this, the specific data snapshot used for the experiments cannot be retrieved if the repository changes, risking link rot and reproducibility failures.

Third, the data schema is implicit. While Section 2.2 describes the adapter protocol, the exact schema of the 350 benchmark instances is not defined. Does it match the SWE-bench JSON schema exactly, or are there new fields for multilingual support? A schema definition or reference to the upstream schema version is required.

Finally, the data cleaning pipeline is opaque. Section 2.3 states "Future-commit history is removed for the seven non-Python languages to prevent leakage." However, the script or method used for this transformation is not referenced. To ensure data integrity, the cleaning script (e.g., `scripts/clean_commits.py`) should be cited or the logic detailed.

These issues are fixable by editing the manuscript text and adding a version tag to the release.
