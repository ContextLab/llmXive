---
action_items:
- id: 049561fdcd68
  severity: writing
  text: Data provenance and licensing are insufficiently documented. The paper claims
    to generate 3,249 tasks from 20 apps (Table 2) but does not specify the license
    of the source apps or the generated dataset. Explicitly state the license (e.g.,
    CC-BY, MIT) for the MobileForge dataset and model weights hosted on HuggingFace
    to ensure reproducibility and legal compliance.
- id: faa7b27c8aa9
  severity: writing
  text: External source link rot risk is high. The paper relies on arXiv preprints
    for nearly all baselines (e.g., '2026' dated papers like gao2026ui, xu2026mobile).
    These links are unstable. Add DOIs or permanent repository URLs (e.g., Zenodo,
    GitHub releases) for all cited works and the project's own code/data to prevent
    future link rot.
- id: 3bdbbf00cab3
  severity: writing
  text: Schema and versioning for the generated curriculum are missing. While Table
    2 lists task counts per app, there is no schema definition for the task format
    (JSON/YAML) or version control information (e.g., git commit hash) for the 3,249-task
    corpus. Include a data card or schema appendix detailing the structure of the
    generated tasks and the exact version of the exploration code used.
artifact_hash: eb6909e8c26be542682832f5d7b13c92b92b728f8b94fb6c9612acad1621be79
artifact_path: projects/PROJ-782-mobileforge-annotation-free-adaptation-f/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T20:15:30.417035Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The paper presents a novel annotation-free adaptation framework but lacks critical data quality documentation required for reproducibility and long-term archival.

**Provenance and Licensing:**
The core contribution relies on a self-generated dataset of 3,249 tasks derived from 20 mobile applications (Table 2, Section Experiments). The manuscript fails to specify the license governing these source applications or the resulting generated dataset. Without a clear license (e.g., CC-BY-4.0, MIT) for the "MobileForge" dataset and the associated models hosted on HuggingFace (referenced in the summary), the data cannot be legally or ethically reused by the community. The authors must explicitly declare the license for all released artifacts.

**Link Rot and External Sources:**
The bibliography is heavily dependent on arXiv preprints, many with future-dated years (e.g., 2026), such as `gao2026ui` and `xu2026mobile`. These links are highly susceptible to link rot. To ensure the paper remains verifiable, the authors should provide permanent identifiers (DOIs) or stable repository URLs (e.g., specific GitHub release tags or Zenodo archives) for all cited works and their own codebase.

**Schema and Version Control:**
While the paper details the *number* of tasks generated, it omits the *schema* of the data. There is no description of the file format (JSON, YAML, etc.) or the specific fields used to represent the "hierarchical feedback" and "curriculum" data. Furthermore, no version control information (e.g., git commit hash) is provided for the data generation pipeline. A data card or an appendix detailing the data schema and the exact version of the `MobileGym` exploration code used to generate the 3,249 tasks is necessary to validate the experimental setup.

**Missing Data Handling:**
The paper mentions filtering tasks based on success rates (Table 4), but does not describe how missing or malformed data during the exploration phase was handled. A brief statement on the robustness of the data collection pipeline against app crashes or invalid states would strengthen the data quality claim.
