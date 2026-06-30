---
action_items:
- id: 2cded2ed9148
  severity: writing
  text: The paper claims to release 'MemGUI-3K' (2,956 trajectories) and 'MemGUI-8B-SFT'
    via HuggingFace (lgy0404/MemGUI-3K, lgy0404/MemGUI-8B-SFT) and GitHub (kwai/MemGUI-Agent).
    However, the manuscript lacks explicit license declarations (e.g., MIT, Apache
    2.0, CC-BY) for the dataset and model weights. Without a stated license, the reproducibility
    and legal usability of the data are undefined.
- id: d5150036cf95
  severity: writing
  text: The dataset construction pipeline (Section 3.2, Fig 2) relies on a 'teacher'
    model (Qwen3-VL-235B-Thinking) and a 'MemGUI-Eval' filter. The paper does not
    provide the specific schema or JSON structure of the resulting MemGUI-3K dataset,
    nor does it detail how 'folded' context states are serialized. A data schema definition
    or a sample data file is required to verify the 'proactive context' claims.
- id: 358238aea568
  severity: writing
  text: External links to the project page (memgui-agent.github.io), HuggingFace repos,
    and GitHub repo are provided in the header and abstract. The review cannot verify
    the current availability or integrity of these resources (link rot check) as the
    paper is a static preprint. The authors must ensure these links are persistent
    (e.g., via Zenodo DOIs) and that the data is actually accessible at the time of
    publication.
- id: a721d8ec73a8
  severity: science
  text: "The paper mentions 'MemGUI-Eval' as a filtering mechanism for the dataset\
    \ (Section 3.2, Table 4). The provenance of this evaluation tool is unclear\u2014\
    is it an open-source script, a proprietary internal tool, or a heuristic? If it\
    \ is not open-sourced alongside the dataset, the reproducibility of the data filtering\
    \ process is compromised."
artifact_hash: 7ba9201f0f49d9384a35f3eca07d4fd8d448c0da222a8a4e9472044b7e857c18
artifact_path: projects/PROJ-781-memgui-agent-an-end-to-end-long-horizon/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T19:26:41.291898Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The review focuses strictly on data quality, provenance, and schema integrity for the MemGUI-Agent paper.

**Data Provenance and Licensing:**
The manuscript explicitly claims the release of a new dataset, **MemGUI-3K** (2,956 trajectories), and a fine-tuned model, **MemGUI-8B-SFT**, providing URLs to HuggingFace (`lgy0404/MemGUI-3K`, `lgy0404/MemGUI-8B-SFT`) and GitHub (`kwai/MemGUI-Agent`). However, the text fails to specify the **license** governing these assets. In the absence of an explicit license (e.g., MIT, Apache 2.0, CC-BY-NC), the legal status of the data is ambiguous, preventing downstream researchers from safely using or redistributing the dataset. This is a critical omission for a paper claiming to advance the field via open data.

**Schema and Data Structure:**
While the paper describes the *concept* of the data (folded history, UI state, recent step record) in Section 2 and 3, it lacks a concrete **data schema**. There is no definition of the JSON structure, field types, or serialization format for the "folded" context states. Without a schema definition or a representative sample file in the appendix or repository, it is impossible to verify if the "proactive context" mechanism is implemented as described or if the data is merely raw trajectories with added text. The "MemGUI-Eval" filter mentioned in Section 3.2 and Table 4 is also opaque; its logic and output format are not detailed, raising concerns about the reproducibility of the dataset curation process.

**External Link Integrity:**
The paper relies heavily on external links for code and data access (e.g., `https://memgui-agent.github.io/`, HuggingFace repos). As a static preprint, the current state of these links cannot be verified for "link rot" or data availability. The authors should ensure these resources are mirrored on a persistent archive (e.g., Zenodo) with a DOI to guarantee long-term accessibility, a standard requirement for data-centric papers.

**Conclusion:**
The paper makes significant claims about data creation and release but fails to provide the necessary metadata (licenses, schemas, provenance details) to validate these claims. The data quality cannot be fully assessed without access to the actual data files and their documentation.
