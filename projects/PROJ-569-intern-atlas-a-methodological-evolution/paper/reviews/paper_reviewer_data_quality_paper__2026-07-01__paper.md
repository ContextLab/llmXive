---
action_items:
- id: 68f3dd4ed794
  severity: science
  text: The paper claims to process 1,030,314 papers from 1965-2025 (Sec 3.2, App
    C.1), but the venue breakdown table (App C.1) only lists editions from 2023-2025,
    totaling ~66k papers. The source of the remaining ~960k papers (1965-2022) is
    not specified, nor is the license status or provenance of this historical corpus.
    Without a clear data source and license for the majority of the dataset, the reproducibility
    and legal validity of the graph are compromised.
- id: 1601fa93b369
  severity: fatal
  text: The evaluation relies on a 'Strata Dataset' of 1,200 papers from 'ICLR 2026',
    'ICML 2025', and 'NeurIPS 2025' (Sec 4.2, App D.3). As of the current date, these
    conferences have not occurred. The paper does not clarify if this data is synthetic,
    projected, or if the dates are typos for past years. If the evaluation data is
    synthetic or fabricated to simulate future events, the claims regarding 'human-alignment'
    and 'publication strata' are invalid.
- id: 15817ee94ffe
  severity: writing
  text: The paper mentions a 'released registry' and 'code release' (App C.1, App
    D.3) but provides no specific URLs, DOIs, or repository paths for the raw data,
    the processed graph, or the evaluation scripts. The HuggingFace link in the title
    page is a placeholder. Data quality review requires access to the actual data
    artifacts to verify schema, missing data handling, and version control.
- id: 5d803ae3c775
  severity: writing
  text: The 'Method entity curation' section (App C.1) states that an LLM expansion
    pass was used to find methods, but it does not specify the version of the LLM
    used for this specific step, the temperature settings, or the exact prompt. Furthermore,
    the 'hand-curated negative-surface list' for alias resolution is not provided.
    This lack of transparency prevents verification of the schema's integrity and
    potential bias in method identification.
artifact_hash: 8cf472ae2a887b5d12e0bb466a1ee80bacbf411e923611b73e3a5325c617cf94
artifact_path: projects/PROJ-569-intern-atlas-a-methodological-evolution/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:12:55.429278Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: full_revision
---

The review focuses strictly on data quality, provenance, and the validity of the datasets used to support the paper's claims.

**Critical Data Provenance and Temporal Fabrication Concerns**
The most severe issue lies in the evaluation data. Section 4.2 and Appendix D.3 describe the "Strata Dataset" as containing papers from "ICLR 2026", "ICML 2025", and "NeurIPS 2025". Given that the current date precedes these conference cycles, these papers cannot exist as real, published artifacts. The paper fails to explicitly state whether this data is synthetic, simulated, or if the dates are erroneous. If the "human-alignment" and "publication strata" results (Table 1, Figure 4d) are derived from synthetic or fabricated future data, the central claim that Intern-Atlas aligns with expert consensus on *real* scientific quality is unsupported. This constitutes a potential fabrication of input data for the evaluation phase, which is a fatal flaw for a data-centric infrastructure paper.

**Corpus Inconsistency and Missing Provenance**
The abstract and Section 3.2 claim the graph is built from 1,030,314 papers spanning 1965–2025. However, Appendix C.1 ("Corpus, PDF Pipeline") provides a venue breakdown table that only lists editions from 2023, 2024, and 2025, summing to approximately 66,431 papers. The source, license, and processing pipeline for the remaining ~960,000 papers (covering 1965–2022) are entirely absent. Without a clear citation to the source of this historical corpus (e.g., specific arXiv dumps, Semantic Scholar Open Research Corpus, or publisher archives) and their associated licenses, the legal and reproducibility status of the primary artifact is unclear.

**Lack of Artifact Accessibility**
The paper repeatedly references a "released registry," "code release," and "supplementary material" (e.g., Appendix C.1, D.3) but provides no functional links. The HuggingFace link in the correspondence section is a placeholder (`https://huggingface.co/datasets/OpenRaiser/Intern-Atlas`), and the GitHub link is commented out. For a paper claiming to provide a "foundational data layer," the inability to access the raw data, the schema definitions, or the version control history of the graph prevents any independent verification of data quality, missing-data handling, or schema consistency.

**Method Curation Transparency**
While the paper describes a two-stage method curation process (hand-curated seed + LLM expansion), it lacks the specific prompts, model versions, and the "manually curated negative-surface list" mentioned in Appendix C.1. This opacity makes it impossible to audit the alias resolution schema or assess potential biases in how methods are identified and grouped, which is critical for the integrity of the graph's nodes.

In summary, the paper relies on evaluation data that appears to be temporally impossible (future conferences) and fails to provide the provenance for the majority of its training corpus or access to the resulting artifacts. These issues prevent the validation of the data quality claims.
