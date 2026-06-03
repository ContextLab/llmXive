---
action_items:
- id: 32b020d36d3e
  severity: writing
  text: Add explicit license information for all source datasets (MultiWOZ, SGD, ESConv,
    AnnoMI) to clarify the legal status of the derived corpus.
- id: efc3602b562d
  severity: writing
  text: Provide a direct download link or repository path for the constructed A2UI
    training corpus in the metadata section, or clarify if it is not public.
- id: ec87ba4a30d4
  severity: writing
  text: Archive the A2UI v0.8 schema specification (e.g., in the GitHub repo) to prevent
    link rot of the external URL cited in the bibliography.
- id: 0dd14e41c01e
  severity: science
  text: Briefly discuss the 85 validation-failed samples to ensure their exclusion
    does not introduce systematic bias against complex interaction patterns.
artifact_hash: 64f9753c508342ff47b0fefdddb7219cc59ae325dbfacf0e2b9d4340a33d4e53
artifact_path: projects/PROJ-629-macaron-a2ui-a-model-for-generative-ui-i/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-03T06:26:08.209577Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The paper describes a robust pipeline for constructing a Generative UI corpus, but several data quality and provenance details require clarification to ensure long-term reproducibility and legal compliance.

First, **data provenance and licensing** are not fully specified. Section 4 cites MultiWOZ, SGD, ESConv, and AnnoMI as source corpora. However, the paper does not state the licenses governing these datasets (e.g., CC-BY, MIT, Research Only). Since the authors claim to release a derived corpus ("We release the models, benchmark, and evaluation protocol" in Abstract), the legal status of the training data depends on the permissiveness of the source licenses. Without this, downstream users cannot verify if redistribution of the annotated data is permitted. Please add a licensing statement for each source dataset and the derived corpus.

Second, **artifact accessibility** is inconsistent. The metadata block links to HuggingFace models and a GitHub benchmark, but there is no explicit link to the training corpus itself (`Sections/4-data.tex`). If the corpus is public, add the URL to the metadata. If it is not public due to licensing, state this clearly to manage expectations regarding reproducibility.

Third, **schema versioning** relies on an external URL (`a2ui_v08` in `colm2026_conference.bib`). Relying on `a2ui.org` introduces a risk of link rot. To safeguard the evaluation protocol, the specific schema version used (v0.8) should be archived within the GitHub repository or a permanent archive (e.g., Zenodo).

Finally, **data filtering bias** is not addressed. Section 4 notes that 85 samples (0.8%) failed validation after three retries. It is unclear if these failures correlate with specific interaction types (e.g., complex multi-turn flows). Excluding them without analysis risks biasing the training set toward simpler patterns. A brief discussion on the nature of these failures is recommended.

These revisions will strengthen the data quality claims and ensure the work remains reproducible.
