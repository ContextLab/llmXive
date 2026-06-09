---
action_items:
- id: 910de45a28ac
  severity: writing
  text: Explicitly state the license (e.g., CC-BY, MIT) for the source datasets (Oops,
    FineVideo) and the newly constructed intervention dataset in Appendix app:assets.
- id: 40d29ff7804d
  severity: writing
  text: Add version numbers or commit hashes for all external evaluation benchmarks
    (VGGSoundSync, Video-MME, etc.) to ensure reproducibility in Section 4.1.
- id: 93e57b2083e8
  severity: writing
  text: Clarify the data release mechanism (e.g., supplementary material, specific
    URL) and access restrictions for the Thud diagnostic assets in Appendix app:assets.
artifact_hash: e83058c54d1a49095166f0ef2ff7177a4db8d52f3626563ad7ae59fa949315e9
artifact_path: projects/PROJ-610-https-arxiv-org-abs-2605-16403/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-09T10:31:51.211276Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on data quality, provenance, and reproducibility. The paper introduces a diagnostic framework (\Thud) and alignment recipe using specific datasets (Oops, FineVideo) and benchmarks. While the methodology for data construction is clear, critical metadata regarding data licensing and versioning is missing, which impacts long-term reproducibility and compliance.

**Dataset Provenance and Licensing**
In Section 3.1 (`sec:dspi`), the authors cite the Oops dataset~\cite{Epstein2019OopsPU} and FineVideo~\cite{Farre2024FineVideo}. However, the specific versions or licenses of these source datasets are not declared. Appendix `app:ethics-impact` states data comes from "public or properly licensed sources," but this is a general claim rather than a specific declaration. For the new intervention dataset (Shift, Mute, Swap), Appendix `app:assets` describes the assets but omits a license for the derived data (e.g., CC-BY-NC, MIT). Without explicit licensing, downstream users cannot legally or ethically reuse the diagnostic assets.

**Version Control and Benchmarks**
Section 4.1 (`ssec:setup`) lists evaluation benchmarks including VGGSoundSync, Video-MME, and LVBench. The bibliography provides DOIs or URLs, but the specific versions or commit hashes of these benchmarks are not recorded. Benchmarks like Video-MME often update over time; without a version pin (e.g., "v1.0"), results cannot be exactly replicated. Similarly, the intervention pipeline in Section 3.2 (`sec:AAPC`) relies on specific annotation tolerances ($\epsilon_v, \epsilon_a$), but the raw data schema is not explicitly defined in a machine-readable format (e.g., JSON schema) in the supplementary material description.

**Data Release Transparency**
The title page links to a Website, Code, and Model, but Appendix `app:assets` does not confirm if the intervention dataset is included in these links or requires separate access. The text states, "If releasing data or code, we will document intended use," which suggests the release might be pending or conditional. For a data-quality review, the availability and license of the *created* data must be concrete at submission time.

To address these gaps, please update the manuscript to explicitly list dataset licenses, pin benchmark versions, and clarify the release status of the Thud assets. These are writing-level fixes that significantly improve data integrity.
