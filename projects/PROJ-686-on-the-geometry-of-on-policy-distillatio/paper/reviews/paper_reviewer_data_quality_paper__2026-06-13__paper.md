---
action_items:
- id: 03ab5ad3f665
  severity: writing
  text: Explicitly list the specific open-source licenses (e.g., MIT, Apache 2.0)
    for all external datasets and checkpoints mentioned in Appendix Artifact Use,
    rather than stating only that terms were checked.
- id: 6f4d1eef397a
  severity: writing
  text: Provide a data schema or manifest for the processed analysis artifacts (e.g.,
    the weight delta matrices and checkpoint hashes) to enable independent verification
    of the parameter-space diagnostics.
- id: 5ccfa868a226
  severity: writing
  text: Replace unstable external links (e.g., the Notion URL for DeepCoder in bibliography)
    with persistent identifiers (DOI or arXiv ID) to mitigate link rot risks.
artifact_hash: 131dbc2ce86fd7fa8c00d7dd55a7501ac648ec7bf3f89711e549ef82e5ed9b1b
artifact_path: projects/PROJ-686-on-the-geometry-of-on-policy-distillatio/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-13T00:58:55.926327Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

This review evaluates the data quality documentation regarding provenance, licensing, schema, and external source stability as presented in the manuscript text.

## Provenance and Licensing

The manuscript provides a strong foundation for data provenance in the Appendix (sections/appendix.tex). Section Artifact Use explicitly states that publicly available checkpoints and datasets (Qwen3, dapo-math-17k, Dolci-Think SFT) were used. However, the statement We checked the public license or usage terms... where available is insufficient for rigorous reproducibility. The specific license types for dapo-math-17k (cited as yu2025dapoopensourcellmreinforcement), DeepCoder, and LiveCodeBench are not enumerated. Reviewers must verify compatibility of these licenses with the intended distribution of derived analysis artifacts.

## Schema and Artifacts

While the paper describes the method of computing weight deltas (Delta W), there is no accompanying data schema or manifest for the processed analysis artifacts. The text references specific checkpoint identifiers (e.g., iter_0005375 in sections/appendix.tex), which is excellent for version control. However, without a schema defining the structure of the stored Delta W matrices or the exact filtering applied to the training datasets (e.g., handling of incomplete rollouts), independent replication of the diagnostic plots (e.g., figures/intrinsic_metrics_3panel.pdf) is hindered. The Artifact Use section should be expanded to include a link to a data manifest or repository containing the processed analysis data.

## Link Rot and External Sources

The bibliography contains several URLs that are susceptible to link rot. Specifically, the deepcoder2025 entry relies on a Notion blog URL. External technical reports should be prioritized via arXiv or DOI where possible to ensure long-term accessibility. The lu2025onpolicydistillation entry also uses a blog URL. While acceptable for preprints, archival stability should be noted.

## Conclusion

The paper adequately describes the source data but lacks the granular documentation required for full data quality verification. Specific license declarations, analysis artifact schemas, and persistent identifiers are required to meet data quality standards for publication.
