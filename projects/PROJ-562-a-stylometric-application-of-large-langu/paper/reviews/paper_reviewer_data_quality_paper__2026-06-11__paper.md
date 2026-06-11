---
action_items:
- id: bbbe0e117906
  severity: writing
  text: Project Gutenberg corpus version and download date not specified (Sec. 2.1).
    Texts may change over time, affecting reproducibility.
- id: 882dde832071
  severity: writing
  text: External GitHub repository link should include archive identifier or DOI for
    permanence against link rot.
- id: 1a15cdf99f6e
  severity: writing
  text: GPT-2 tokenizer version and Hugging Face Transformers library version not
    documented in Methods section.
artifact_hash: 148021f63314c6cbe2b6159eaaaecc4e6c793ec5541ddbe74681664a10cdde19
artifact_path: projects/PROJ-562-a-stylometric-application-of-large-langu/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-11T16:36:49.211134Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The paper demonstrates reasonable attention to data quality but has several gaps in provenance documentation that could affect reproducibility.

**Provenance & Licensing**: Section 2.1 (main-llmxive.tex, lines 245-265) correctly identifies Project Gutenberg as the data source and notes public domain status. However, no download date, version, or specific corpus snapshot is provided. Gutenberg texts can be updated post-publication, which introduces ambiguity about which exact text versions were analyzed.

**Schema & Preprocessing**: The preprocessing pipeline is well-described (stripping metadata, lowercasing, removing non-ASCII). The Appendix provides book titles and token counts (lines 900-1050), which aids verification. However, the exact GPT-2 tokenizer version and Hugging Face Transformers library version are not documented (Methods, lines 280-320). Since tokenization can vary across versions, this affects reproducibility.

**External Dependencies**: The "Data and code availability" section (main-llmxive.tex, line 850) links to a GitHub repository without an archive identifier (e.g., Zenodo DOI, arXiv-sourced snapshot). This creates potential link rot risk. For long-term reproducibility, the repository should be archived with a persistent identifier.

**Missing Data**: The random seed values used for the 10 repetitions are not listed (only that 10 seeds were used). While this doesn't affect the conclusion, it prevents exact replication of the experimental runs.

**Recommendations**:
1. Add Project Gutenberg download date/version to Section 2.1
2. Archive the code repository with a DOI (Zenodo/figshare) and update the availability statement
3. Specify exact versions of transformers library and tokenizer
4. Consider listing random seed values in Supplementary Materials

These are minor writing/documentation issues that do not undermine the scientific claims but should be addressed for full reproducibility.
