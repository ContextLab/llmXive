---
action_items:
- id: 574d87415a88
  severity: science
  text: Clarify license compatibility for Harry Potter-derived probes under CC-BY-4.0,
    as the source text is copyrighted (Appendix \S\ref{app:datapoint}).
- id: 583a8599bb91
  severity: writing
  text: Specify a dataset version number (e.g., v1.0) to ensure reproducibility of
    the benchmark split and schema.
- id: 31fb296e3216
  severity: writing
  text: Report the validation drop rate (number of probes marked 'unavailable' vs.
    total generated) to assess data quality filtering rigor (Appendix \S\ref{app:probe-details}).
- id: 234e6fe063d0
  severity: writing
  text: Verify the arXiv ID date (2606.05553 implies June 2026) to ensure provenance
    links are valid and not simulated.
artifact_hash: 571d3401a83d0a75eab9bacc6292347c4c0034a87d0b29427ea4178c11f1a6c3
artifact_path: projects/PROJ-670-arcane-do-role-playing-language-agents-s/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-28T09:57:46.325078Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The paper provides a detailed schema for the ArcANE dataset in Appendix \S\ref{app:datapoint}, defining Character Arc and Probe records with clear JSON keys. The split between training and evaluation sets is well-documented in Table \ref{tab:data_stats}, with human validation explicitly applied to the evaluation slice (\S\ref{sec:dataset}). However, several data quality concerns require attention before publication.

First, the license declaration in Appendix \S\ref{app:datapoint} states artifacts will be distributed under CC-BY-4.0. However, the dataset includes probes derived from *Harry Potter*, which is explicitly noted as "non-Gutenberg" (\S\ref{sec:additional}). Releasing copyrighted text derivatives under a permissive public license may create legal conflicts that affect data availability and reproducibility. The authors must clarify the scope of the CC-BY-4.0 license regarding copyrighted source material.

Second, while the validation pipeline is described (Stage iii human annotators), the paper does not report the drop rate of probes marked `unavailable` during the validation pass (Appendix \S\ref{app:probe-details}). Knowing how many generated probes failed the Q-Voice or Q-PhaseFit checks is essential to assess the quality of the final benchmark.

Third, no dataset version number (e.g., v1.0) is specified. Given the automated construction pipeline, versioning is critical for reproducibility.

Finally, the arXiv ID `2606.05553` corresponds to June 2026, which is in the future relative to the current date. This provenance anomaly should be corrected to ensure the paper can be properly archived and cited.
