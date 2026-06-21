---
action_items:
- id: c14db4027db1
  severity: writing
  text: "Add a clear Data Availability statement describing where the three constructed\
    \ datasets (Interleave\u2011Planner\u2011SFT\u201180k, Interleave\u2011Critic\u2011\
    SFT\u2011112k, Interleave\u2011Critic\u2011RL\u201113k) can be downloaded, including\
    \ persistent URLs (e.g., Zenodo, HuggingFace) and the exact file formats."
- id: addb3e644072
  severity: writing
  text: "Specify the license under which the released datasets and any code (e.g.,\
    \ the data\u2011filtering pipeline, training scripts) are distributed. Use an\
    \ OSI\u2011approved license and include the license text in the repository."
- id: 8546eda2f319
  severity: writing
  text: Provide a detailed schema for each dataset (column names, data types, example
    rows) in the appendix or a separate markdown file so that downstream users can
    validate the format.
- id: c86e5779165c
  severity: writing
  text: Document the random seeds, software versions (Python, PyTorch, Transformers)
    and hardware configuration used for data generation and filtering to ensure reproducibility.
- id: a981b3566bed
  severity: writing
  text: "Include version control information (e.g., git commit hash, tag) for the\
    \ code that generated the datasets and trained the agents. This can be added to\
    \ the paper\u2019s footnote or a README."
- id: 3714dd79ed97
  severity: writing
  text: "Replace bare URLs (e.g., https://github.com/zhengdian1/InterleaveThinker,\
    \ https://huggingface.co/InterleaveThinker) with archived links (e.g., via archive.org)\
    \ or DOI\u2011based references to mitigate link rot."
- id: f961de54756c
  severity: writing
  text: "Clarify how missing or low\u2011quality synthetic samples were handled during\
    \ filtering (e.g., thresholds, manual inspection) and provide statistics on how\
    \ many samples were discarded at each stage."
- id: 4953c0642c65
  severity: science
  text: "If the datasets contain copyrighted material (e.g., images from external\
    \ sources), describe the provenance and obtain appropriate permissions or provide\
    \ a statement of fair\u2011use compliance."
artifact_hash: 8426723cc1e7037d7086c3e739b487a916d863fe0fa9c20614721aae3b7449c1
artifact_path: projects/PROJ-699-interleavethinker-reinforcing-agentic-in/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T18:38:29.524773Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript focuses on a multi‑agent pipeline for interleaved generation but provides very limited information about the underlying data assets, which raises several data‑quality concerns.

**Provenance & Licensing**  
The three core datasets (Interleave‑Planner‑SFT‑80k, Interleave‑Critic‑SFT‑112k, Interleave‑Critic‑RL‑13k) are generated synthetically using proprietary models (Gemini 2.5 Pro, Nano Banana Pro). However, the paper does not disclose where these datasets are hosted, nor under what license they are released. Without an explicit data‑availability statement and a clear license (e.g., CC‑BY‑4.0, MIT), readers cannot legally reuse or redistribute the data, and the provenance chain is opaque.

**Schema & Documentation**  
Section 3.2 describes the data‑construction pipeline but omits a concrete schema. It is unclear what fields each record contains (e.g., `instruction`, `prompt`, `image_path`, `score`, `judgment`). Providing a table of column names, data types, and example rows (or a JSON schema) would enable downstream validation and integration.

**Missing‑Data Handling**  
The filtering steps (step‑filtering, variance‑based split, judgment balancing) are described qualitatively, but quantitative details are missing. The paper should report the number of raw trajectories generated, how many were discarded at each filtering stage, and the criteria (score thresholds) used. This transparency is essential for assessing potential bias introduced by aggressive filtering.

**Version Control & Reproducibility**  
All code that orchestrates data generation, filtering, and RL training is referenced only via a GitHub URL in the author block. There is no commit hash, tag, or release identifier. Including a specific git commit (or a DOI for a Zenodo snapshot) would guarantee that future readers can retrieve the exact code version used for the reported experiments.

**Link Rot & External Resources**  
The manuscript contains several bare URLs (e.g., the project’s GitHub repo, HuggingFace model page, and external model references such as Gemini 2.5 Pro). These links may become unavailable over time. Providing archived versions (via archive.org) or DOI‑based citations would improve long‑term accessibility.

**Licensing of External Content**  
Synthetic images are produced by proprietary generators. If any of the training data for those generators includes copyrighted material, the authors should state how they ensured compliance (e.g., using public‑domain sources, obtaining licenses, or invoking fair‑use arguments). This is especially important because the downstream datasets inherit any licensing constraints from the source models.

**Actionable Recommendations**  
- Add a Data Availability section with persistent download links and licensing information.  
- Publish a schema definition (CSV/JSON) for each dataset in the supplementary material.  
- Include detailed statistics on the filtering pipeline (counts, thresholds).  
- Record the exact software stack (Python 3.x, PyTorch x.x, Transformers x.x) and random seeds.  
- Reference a specific git commit or release tag for the codebase.  
- Use archived URLs or DOIs for all external resources to guard against link rot.  
- Clarify any copyright considerations for the synthetic images.

Addressing these points will substantially improve the paper’s data‑quality transparency, reproducibility, and legal reusability, bringing it in line with community standards for open multimodal research.
