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
reviewed_at: '2026-06-09T11:05:06.072717Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

**Re-Review: Data Quality**

This is a re-review against the prior data-quality action items. I find that **none of the four prior concerns have been adequately addressed** in the current revision.

**Unaddressed Action Items:**

1. **Licensing terms (ID: 5ccfcda4f405, science)**: The NeurIPS Paper Checklist answers "\answerYes{}" to the licensing question with the justification "Credited with URLs and package names throughout paper and supplemental materials." This does not address the specific concern about redistribution rights for source datasets with restricted licenses (e.g., CheXpert, CBIS-DDSM). The MulTaBench bundle licensing remains unclear.

2. **Persistent archive link (ID: c5c264416b61, writing)**: Section 5 still cites the generic Kaggle profile link (https://www.kaggle.com/chico89/datasets). No Zenodo DOI or persistent archive URL has been added. Link rot risk persists.

3. **Data loss transparency (ID: 9b06806e6bfc, science)**: Appendix e002 states "Rows with absent or corrupt images are dropped" but provides no quantitative reporting of how many rows were dropped or what percentage of the original candidate pool was lost during curation.

4. **Availability contradiction (ID: f6b95d3bc51e, writing)**: Section 5 states "Uploaded to Kaggle" (present tense), while the Checklist states "MulTaBench will be uploaded to Kaggle upon acceptance" (future tense). This contradiction remains unresolved and creates ambiguity for reviewers attempting to access the benchmark.

**No New Issues Introduced:** The revision does not introduce new data-quality concerns beyond the unaddressed prior items.

**Recommendation:** All four action items must be resolved before acceptance. The licensing clarification and data-loss reporting are science-severity items requiring substantive documentation; the link and availability issues are writing-severity but critical for reproducibility.
