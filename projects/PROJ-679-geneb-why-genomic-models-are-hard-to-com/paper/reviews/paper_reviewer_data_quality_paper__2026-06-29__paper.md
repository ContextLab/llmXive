---
action_items:
- id: 57325591d8c0
  severity: writing
  text: 'The manuscript does not specify a license for the GENEB benchmark data or
    code (Section: Limitations/Appendix). Please add a license statement (e.g., MIT,
    CC-BY) to ensure reuse.'
- id: 2c9a323da90f
  severity: writing
  text: The arXiv ID `2606.04525` in the metadata corresponds to a future date (June
    2026). Please verify and correct the submission ID for provenance accuracy.
- id: 83f402c6fb80
  severity: science
  text: Appendix `app:excluded_models` notes 25% of models excluded due to 'Private
    weights' or 'Broken code'. Please discuss how this selection bias impacts the
    benchmark's representativeness of the field.
- id: 8229a08b0268
  severity: writing
  text: Task sources (NT, GUE, GB) are cited by name but lack specific versioned URLs
    or DOIs in `tab:task_groups`. Please provide persistent links to the exact dataset
    versions used.
artifact_hash: 043e93d2fab619e0251c0029f296fc31d53c712bc78a466a1a30d67af8b711e1
artifact_path: projects/PROJ-679-geneb-why-genomic-models-are-hard-to-com/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T02:36:41.852515Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript presents a comprehensive benchmark (GENEB) but exhibits several data quality and provenance gaps that require attention before publication.

**Provenance and Metadata:**
The paper metadata lists an arXiv ID `2606.04525` (Section: Paper provenance). This ID implies a submission date of June 2026, which is in the future relative to the current context. This discrepancy undermines the provenance verification of the manuscript itself. Please correct the arXiv ID to match the actual submission record. Additionally, the bibliography relies heavily on preprints (bioRxiv, arXiv) without DOIs for many entries (e.g., `Zhou2025.01.30.635558`). While common in fast-moving fields, providing DOIs or stable URLs where available would improve long-term citation stability.

**Data Availability and Licensing:**
There is no explicit license statement for the GENEB benchmark data, code, or evaluation scripts in the text (e.g., `Limitations` or `Appendix`). Without a clear license (e.g., MIT, Apache 2.0, CC-BY), the reproducibility and reuse of the benchmark are legally ambiguous. Please add a license declaration to the repository or manuscript.

**Schema and Versioning:**
The task taxonomy in `tab:task_groups` (Appendix) aggregates tasks from nine benchmarks (NT, GUE, GB, etc.). However, it does not specify the exact version or commit hash of these external datasets used. Benchmarks like GUE or Nucleotide Transformer may have evolved since the cited papers were published. To prevent link rot and ensure exact replication, please provide persistent URLs or version identifiers for the specific dataset splits used in GENEB.

**Selection Bias:**
Appendix `app:excluded_models` indicates that 13 out of 53 surveyed models (approx. 25%) were excluded due to "Private weights," "Broken code," or "Missing extraction code." While this is a practical constraint, the manuscript should explicitly discuss how this exclusion rate impacts the benchmark's representativeness of the current genomic modeling landscape. If significant state-of-the-art models are inaccessible, the aggregate conclusions may be skewed toward open-source models.

Addressing these data quality issues will strengthen the reproducibility and long-term utility of the GENEB benchmark.
