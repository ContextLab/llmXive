---
action_items:
- id: de3c7361cfbe
  severity: fatal
  text: The manuscript does not provide a clear, verifiable description of the pretraining
    data corpus (e.g., source documents, licensing terms, filtering criteria). This
    omission makes it impossible to assess data provenance, legality, or potential
    bias.
- id: 3e46b0bda9f3
  severity: fatal
  text: No explicit data license information is supplied for the training data or
    the released multimodal model checkpoint. Include a statement of the licenses
    governing all datasets and model weights.
- id: 30af58cf3875
  severity: writing
  text: "The paper references external resources (e.g., the inference kernel at https://github.com/MiniMax-AI/MSA\
    \ and the released model at https://huggingface.co/MiniMaxAI/MiniMax-M3) without\
    \ indicating the version or commit hash used for the experiments, risking reproducibility\
    \ loss and link\u2011rot."
- id: 37ad3b4b30c0
  severity: writing
  text: There is no schema or metadata description for the multimodal training data
    (image/video tokens). Provide a data sheet that details modalities, tokenization,
    and any preprocessing steps.
- id: 887f0f68633a
  severity: writing
  text: "The experimental section mentions a 3\u202FT\u2011token training budget but\
    \ does not disclose how many tokens come from each source (text vs. image vs.\
    \ video). This hinders assessment of dataset composition and potential modality\
    \ imbalance."
- id: 5dc70e28b8a4
  severity: writing
  text: "The appendix contains several figures (e.g., Fig\u202F\\ref{fig:vis-selection})\
    \ that rely on visualizations of internal model states, but the raw data files\
    \ used to generate these plots are not archived or referenced, making independent\
    \ verification impossible."
artifact_hash: f00725508246b024cf4aa3c534e6f6afc166e2aa03bee30b44dd04e950f05991
artifact_path: projects/PROJ-701-minimax-sparse-attention/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-17T16:27:33.989400Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The review focuses exclusively on data‑quality aspects of the submission.  

**Provenance & Licensing**  
The manuscript (see abstract, lines 1‑5) claims a “mixture of text and image/video data” for pretraining a 109 B‑parameter model, yet it never enumerates the constituent datasets, their origins, or the legal permissions under which they are used. This lack of a data‑sheet violates basic provenance standards and prevents downstream users from confirming that the training corpus respects copyright and privacy constraints. Moreover, the paper provides no licensing information for the released model checkpoint hosted on HuggingFace (Section 5, lines 43‑45) or for the kernel code on GitHub (Section 4, lines 12‑14). Without explicit license statements, the community cannot legally reuse or redistribute the artifacts.

**Missing Schema & Metadata**  
The multimodal nature of the training data is emphasized (Section 5, lines 5‑9), but there is no formal schema describing how images or video frames are tokenized, how many tokens per modality are allocated, or what preprocessing pipelines are applied. A concise data‑schema (e.g., JSON/YAML) should be supplied, together with any annotation standards used, to enable reproducibility and to allow auditors to evaluate bias or representation gaps.

**Version Control & Reproducibility**  
References to external code repositories are given as plain URLs (e.g., `https://github.com/MiniMax-AI/MSA`). The paper does not record the specific commit hash, tag, or release version that corresponds to the experiments reported in Figures 2‑5. Given the rapid evolution of open‑source kernels, this omission creates a risk of link‑rot and makes it impossible for reviewers to reconstruct the exact software environment. The same issue applies to the HuggingFace model link; a precise version identifier (e.g., `v1.2.0` or a git SHA) is required.

**Training‑Data Accounting**  
The experimental setup (Section 5.1, lines 7‑12) mentions a “3 T‑token budget” and a “40 B‑token indexer warmup,” but does not break down token counts by source modality or dataset. Without this accounting, it is unclear whether the model’s performance gains stem from the sparse‑attention mechanism or from an unbalanced data mix that could favor certain tasks.

**Missing Raw Outputs for Visual Analyses**  
Figures \\ref{fig:vis-selection} and \\ref{fig:attention-sink} (Appendix A, lines 1‑30) visualize internal selection probabilities and attention sinks. The underlying raw tensors or CSV files are not archived or referenced, preventing independent verification of the reported patterns. Providing these data (or a script to regenerate them) is essential for transparency.

**Recommendations**  
To bring the paper into compliance with data‑quality best practices, the authors should:  
1. Include a detailed data‑sheet enumerating all training corpora, their licenses, and any filtering steps.  
2. State the exact software version (commit SHA or release tag) for both the kernel repository and the released model checkpoint.  
3. Publish a schema describing multimodal tokenization and preprocessing pipelines.  
4. Provide a token‑budget breakdown by modality and source dataset.  
5. Archive the raw data used for the visualizations (or supply reproducible generation scripts).  

Addressing these points will substantially improve the paper’s reproducibility, legal clarity, and overall trustworthiness.
