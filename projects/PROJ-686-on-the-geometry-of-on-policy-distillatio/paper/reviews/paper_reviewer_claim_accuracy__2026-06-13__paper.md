---
action_items:
- id: 62611a7b0618
  severity: writing
  text: Table 1 lists 'Published reference points' (e.g., Klear-Reasoner, Polaris)
    without bibliographic citations. Add references to the original releases or papers
    for these checkpoints to support the claim of their existence and properties.
- id: ad829f59d1cd
  severity: writing
  text: Section app:experimental-details cites `olmo2025olmo3` for 'Dolci-Think SFT
    data'. Verify if this data is explicitly described in the Olmo 3 paper or if a
    separate dataset citation is required to support the data provenance claim.
- id: 013b022b124e
  severity: writing
  text: LiveCodeBench v5 is cited using the 2024 Jain et al. paper. If v5 is a newer
    version not covered by the 2024 publication, update the citation or clarify the
    version relationship to ensure accuracy.
artifact_hash: 131dbc2ce86fd7fa8c00d7dd55a7501ac648ec7bf3f89711e549ef82e5ed9b1b
artifact_path: projects/PROJ-686-on-the-geometry-of-on-policy-distillatio/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-13T00:50:31.937172Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper makes several factual claims regarding parameter-space geometry and training dynamics. Most claims about SFT and RLVR geometry are well-supported by the cited literature (e.g., `zhu2025pnt` for off-principal updates, `liu2026liftveiltruthprincipal` for SFT density). The core empirical claims (subspace locking, objective sensitivity) are supported by the provided figures and tables within the manuscript.

However, there are specific citation accuracy issues regarding data and checkpoint provenance:

1.  **Table 1 References:** The table includes "Published reference points" such as `Klear-Reasoner-8B-SFT`, `UniReason-14B-think-SFT`, and `Polaris-4B-Preview`. These are presented as factual baselines but lack corresponding entries in the bibliography. To support the claim that these checkpoints exist and have the reported properties, they must be explicitly cited (e.g., pointing to their technical reports or release notes).

2.  **Dataset Citation:** In Appendix E (Experimental Details), the text states, "the SFT anchor is trained on Dolci-Think SFT data \cite{olmo2025olmo3}". The cited work `olmo2025olmo3` is the Olmo 3 Technical Report. If "Dolci-Think" is a specific dataset distinct from the model architecture, citing the model paper may be imprecise. Please verify if the dataset is formally described in this paper or provide a direct citation for the data release.

3.  **Versioning:** The text references "LiveCodeBench v5" while citing the 2024 `jain2024livecodebenchholisticcontaminationfree` paper. If version 5 was released after the 2024 publication, the citation should be updated or clarified to ensure the version claim is accurate.

These issues do not invalidate the core findings but require correction to ensure full bibliographic accuracy and reproducibility.
