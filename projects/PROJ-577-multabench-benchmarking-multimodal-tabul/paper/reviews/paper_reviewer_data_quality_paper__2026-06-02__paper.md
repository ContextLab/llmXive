---
action_items:
- id: 5ccfcda4f405
  severity: science
  text: Clarify the licensing terms for the MulTaBench bundle. Explicitly confirm
    redistribution rights for source datasets (e.g., CheXpert, CBIS-DDSM) which often
    have restricted licenses.
- id: c5c264416b61
  severity: writing
  text: Replace the generic Kaggle profile link (https://www.kaggle.com/chico89/datasets)
    with a persistent archive link (e.g., Zenodo DOI or specific dataset collection
    URL) to prevent link rot.
- id: 9b06806e6bfc
  severity: science
  text: Report the percentage of rows dropped due to missing/corrupt images or files
    during curation to ensure transparency on data loss.
- id: f6b95d3bc51e
  severity: writing
  text: Reconcile the contradiction between Section 5 ("Uploaded to Kaggle") and the
    Checklist ("upon acceptance"). Specify current availability status for reviewers.
artifact_hash: 6787a87df841d43fd2785f288cbdae2d1c09b5ec14bf84bfd0cf81559d785c80
artifact_path: projects/PROJ-577-multabench-benchmarking-multimodal-tabul/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-02T11:17:50.752881Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

**Data Quality Review**

The MulTaBench paper presents a substantial curation effort for multimodal tabular data. However, several data quality and provenance issues require clarification before the benchmark can be reliably reused.

**Provenance and Licensing**
Section 5 and Appendix C state that all 40 datasets are "uploaded to Kaggle under the MulTaBench organization." While re-hosting aids access, it introduces licensing risks. Many source datasets (e.g., CheXpert, CBIS-DDSM, Hateful Meme) have specific usage agreements that may prohibit redistribution or require separate registration. The NeurIPS Checklist claims assets are "properly credited and licensed" based on URL citation, but this does not confirm redistribution rights. Please specify the license of the MulTaBench bundle (e.g., CC-BY, MIT) and confirm compliance for each source dataset.

**Link Stability and Version Control**
The abstract and Section 5 cite `https://www.kaggle.com/chico89/datasets`, which points to a user profile rather than a specific dataset collection. This is prone to link rot. Additionally, the Checklist states MulTaBench will be "uploaded to Kaggle upon acceptance," contradicting Section 5's claim that it is already uploaded. For a benchmark paper, data must be immediately accessible. Please provide a persistent archive link (e.g., Zenodo) and clarify the current availability status.

**Data Cleaning Transparency**
Appendix C mentions dropping "Absent/c corrupt files" and "Missing images" but does not quantify this data loss. For reproducibility, report the percentage of rows dropped per dataset. Furthermore, Appendix C notes "structured columns that directly encode the target are dropped." To prevent leakage concerns, list the specific columns removed for each dataset (e.g., in an appendix table).

**Schema Consistency**
Regression targets are discretized into 20 bins for cross-entropy optimization (Appendix C). This alters the original schema and label distribution. Discuss how this transformation impacts the original task definition and whether the discretization thresholds are fixed or dataset-specific.

Addressing these points will ensure the benchmark's long-term usability and legal safety.
