---
action_items:
- id: 5fd9516c78b5
  severity: writing
  text: Explicitly declare the data license (e.g., CC-BY-4.0) for Voices-in-the-Wild-2M
    in Section 3 or Appendix. HuggingFace links alone are insufficient for provenance.
- id: 368c31c040ee
  severity: writing
  text: Resolve the discrepancy between '2.4M synthesized clips' (Section 3) and '2M'
    scale (Table 1). Consistent reporting is required for data reproducibility.
- id: 191536ee1adb
  severity: writing
  text: Provide a persistent archive link (e.g., Zenodo DOI) alongside GitHub/HuggingFace
    to prevent link rot for the dataset and benchmark code.
artifact_hash: b76830428db6f31ab0213200b5916231003e882ec498765fb220acf8020a5333
artifact_path: projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-11T02:21:26.964557Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript presents a substantial new dataset, **Voices-in-the-Wild-2M**, but several data quality metadata issues require correction before publication.

First, **license provenance** is missing. While the authors link to a HuggingFace repository (Section 3, e000), the manuscript text does not explicitly state the license under which the new dataset is released (e.g., CC-BY-4.0, MIT). Without this declaration in the paper itself, downstream users cannot legally ascertain usage rights, violating standard data quality norms for open research artifacts.

Second, there is a **quantitative inconsistency** regarding dataset scale. Section 3 (Overview, e000) states the dataset comprises "**2.4M** synthesized clips," whereas Table 1 (relatedworks, e000) lists the Scale as "**2M**". This discrepancy affects the reproducibility of the reported results and the perceived data volume. The text must be aligned to a single, verified figure.

Third, **schema documentation** is incomplete. Appendix e002 (Table `tab:dg_wgpo_data_schema`) details the JSONL schema for the RL training stage, but the primary dataset schema (audio sampling rate, codec, transcript encoding, metadata fields) is only described narratively in Section 3. A formal schema definition or reference to a schema file should be provided to ensure programmatic usability.

Finally, **link persistence** is a risk. The project relies on GitHub and HuggingFace links (e.g., `github.com/xzf-thu/Voices-in-the-Wild-Bench`). These are volatile; a DOI via Zenodo or OSF is recommended to ensure long-term accessibility for the benchmark and data, preventing link rot that would invalidate future evaluations.

Addressing these metadata gaps will significantly improve the dataset's utility and reproducibility for the community.
