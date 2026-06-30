---
action_items:
- id: 2f7a43fb72bd
  severity: writing
  text: The paper relies on external datasets (e.g., WikiWeb2M, EDR-200, LongBenchV1)
    and models (CEMTM, Qwen3) without providing explicit license terms or version
    hashes in the text or bibliography. Section 5.1 and Appendix A must include specific
    license identifiers (e.g., CC-BY-4.0, Apache 2.0) and commit hashes or version
    numbers for all external data and model weights to ensure reproducibility and
    legal compliance.
- id: 3f9dfd983bbd
  severity: writing
  text: The metadata bank construction (Section 4.1) and training data synthesis (Section
    4.3) involve processing large corpora. The paper lacks a statement on how missing
    data or corrupted chunks were handled during the topic modeling and query generation
    phases. A brief description of data cleaning pipelines or exclusion criteria for
    low-quality chunks is required.
- id: 28a18972256d
  severity: writing
  text: The GitHub link in the Abstract (lines 18-20) and the arXiv URL in the provenance
    section are external dependencies. The paper should verify these links are stable
    and consider archiving the code/data snapshot (e.g., via Zenodo) to prevent link
    rot, ensuring the artifact remains accessible for future review.
artifact_hash: 5e7163c1713464843d620f2c37705ca96ededa7c235cfa3e5a0986f0a19b0aa7
artifact_path: projects/PROJ-766-mcompassrag-topic-metadata-as-a-semantic/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T15:14:08.485565Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript demonstrates a strong focus on methodological innovation but lacks sufficient detail regarding data provenance and licensing, which are critical for reproducibility and legal compliance in data-intensive research.

**Provenance and Licensing:**
In Section 5.1 ("Experimental Setup") and Appendix A ("Benchmark and Baseline Details"), the authors cite multiple external datasets (WikiWeb2M, EDR-200, LongBenchV1, Dragonball) and models (CEMTM, Qwen3-Embedding-4B). However, the specific licenses governing the use of these resources are not explicitly stated in the text or the bibliography. For instance, the license for the WikiWeb2M dataset and the specific version of the CEMTM model weights used are missing. Without explicit license identifiers (e.g., CC-BY-4.0, MIT) and version hashes (e.g., Git commit SHA or HuggingFace model revision), it is impossible to verify if the usage complies with the original terms or to reproduce the exact experimental setup. The bibliography entries for these resources should be augmented with license information where available.

**Missing Data Handling:**
Section 4.1 describes the construction of the "metadata bank" from chunk-level topic distributions, and Section 4.3 details the synthetic training data generation. The paper does not mention how missing data, corrupted chunks, or chunks that fail topic modeling (e.g., due to length or encoding issues) were handled. A brief description of the data cleaning pipeline, including any exclusion criteria for low-quality or incomplete data, is necessary to assess the robustness of the metadata bank.

**External Link Stability:**
The Abstract (lines 18-20) includes a direct link to a GitHub repository. While currently functional, reliance on external URLs without archival backups (e.g., via Zenodo or arXiv source) poses a risk of link rot. The authors are encouraged to provide a persistent archive link or a specific version tag in the repository to ensure the code and data remain accessible for future verification.

**Schema and Version Control:**
While the mathematical schema for the metadata bank is well-defined (Eq. 1), the physical schema of the stored data (e.g., file formats, compression methods, or database structures used for the metadata bank) is not described. Additionally, there is no mention of version control for the topic model centroids or the training data splits. Including a version identifier for the topic model and the training data split would significantly improve the reproducibility of the results.
