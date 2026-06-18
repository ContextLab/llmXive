---
action_items:
- id: b140f5154ca2
  severity: writing
  text: "Add a dedicated Data Card or similar documentation that lists all training\
    \ datasets (e.g., FineWeb, Nemotron\u2011CC, etc.) together with their source\
    \ URLs, version identifiers, licensing terms, and any preprocessing steps applied."
- id: b27c63af2293
  severity: writing
  text: "Correct malformed external links (e.g., the HuggingFace collection URL ending\
    \ with \"}{%\" and any other stray LaTeX markup) and verify that all cited URLs\
    \ resolve; replace broken links with stable, version\u2011pinned references."
- id: cfe08de78f9f
  severity: writing
  text: "Replace placeholder citation keys such as \"\\cite{#1}\" with proper bibliographic\
    \ entries, and ensure every in\u2011text citation corresponds to a complete entry\
    \ in references.bib."
- id: 25fee7a63ea1
  severity: science
  text: "Publish checksums (SHA\u2011256) and explicit version numbers for all released\
    \ model checkpoints (base, Instruct, Thinking) and provide a machine\u2011readable\
    \ manifest (e.g., JSON) describing file formats, tokenizers, and compatibility."
- id: 68f9cfb9b51b
  severity: science
  text: "Describe the handling of missing or filtered data during pre\u2011training\
    \ (e.g., how duplicate or low\u2011quality samples were removed) and provide statistics\
    \ on dataset composition after filtering."
artifact_hash: cb4466a31e7b640ad51d8c2f8310c27b9827d874fc645a40e58bc959301ab98e
artifact_path: projects/PROJ-647-mellum2-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T10:36:53.076481Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

**Data‑quality assessment**

The manuscript provides a thorough technical description of the Mellum 2 model but falls short on several data‑centric aspects that are essential for reproducibility and responsible reuse.

1. **Provenance & Licensing** – While the paper references many external datasets (FineWeb, Nemotron‑CC, OLMo‑3 Longmino, etc.), it does not disclose the exact versions, release dates, or licenses of these corpora. No data‑card or similar documentation is included, leaving readers unable to verify that the training data are legally reusable under the claimed Apache 2.0 model release. This omission also hampers downstream auditing of potential copyrighted or sensitive content.

2. **Schema & Metadata** – The released checkpoints are mentioned (“all checkpoints … are released under Apache 2.0”) but no schema is provided for the accompanying files (e.g., tokenizer vocab, config JSON). Without a manifest describing file formats, expected tokenization, and model‑parallel layout, users may encounter incompatibilities when loading the models.

3. **Missing‑data Handling** – The paper discusses long‑context extension and MoE load‑balancing loss, yet it gives no quantitative description of how missing or low‑quality training samples were filtered (e.g., duplicate removal, language detection). A brief summary of the filtering pipeline and resulting dataset statistics (total tokens after cleaning, per‑domain token counts) would strengthen the claims about data quality.

4. **Version Control & Reproducibility** – No explicit commit hashes, branch names, or release tags are provided for the codebase that generated the models. The figures and tables reference “Fig. X” but the underlying data (e.g., RULER scores, loss curves) are not released, making it impossible to independently reproduce the plots.

5. **Link Rot & URL Robustness** – Several external URLs appear malformed (e.g., the HuggingFace collection link ending with “}{%”) and some citations use placeholder keys such as “\cite{#1}”. These issues risk link rot and undermine the paper’s credibility. All URLs should be verified and, where possible, pinned to a specific version (e.g., using DOI or archive.org snapshots).

6. **Safety & Ethical Data Considerations** – The safety evaluation is presented, but there is no discussion of how potentially harmful content was mitigated during data collection. Including a brief ethical review of the training corpus would align the work with emerging standards for responsible AI.

Overall, the technical contributions are solid, but the manuscript lacks the data‑quality scaffolding needed for transparent, reproducible research. Addressing the action items above will bring the paper into compliance with best practices for dataset documentation, licensing clarity, and artifact versioning.
