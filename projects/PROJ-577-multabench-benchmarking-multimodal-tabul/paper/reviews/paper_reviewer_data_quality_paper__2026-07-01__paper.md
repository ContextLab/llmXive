---
action_items:
- id: 926badf3b5e5
  severity: science
  text: The paper presents a significant benchmarking effort, MulTaBench, but raises
    critical concerns regarding data provenance, version control, and the handling
    of missing data that threaten the reproducibility of the results. First, the provenance
    and link rot issue is severe. While the authors propose uploading the benchmark
    to Kaggle to address the "fragility of external image links" (Section 4, Appendix
    A.2), the manuscript currently relies on a mix of unstable URLs (Figshare, various
    Kaggle data
artifact_hash: 28e097e31933ecce294eb34fd92a9e53c4dcbbab117fcc0a77af75a314777084
artifact_path: projects/PROJ-577-multabench-benchmarking-multimodal-tabul/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:51:40.945987Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: full_revision
---

The paper presents a significant benchmarking effort, MulTaBench, but raises critical concerns regarding data provenance, version control, and the handling of missing data that threaten the reproducibility of the results.

First, the **provenance and link rot** issue is severe. While the authors propose uploading the benchmark to Kaggle to address the "fragility of external image links" (Section 4, Appendix A.2), the manuscript currently relies on a mix of unstable URLs (Figshare, various Kaggle datasets, OpenML) for the 40 datasets. Appendix A.2 explicitly admits that many original links are dead (e.g., the Seattle Airbnb dataset) and that datasets were manually curated to recover them. Relying on a dynamic Kaggle collection without a permanent, versioned archive (e.g., a Zenodo DOI pointing to the *exact* CSV and image snapshots used in the experiments) creates a high risk of data drift. If the underlying Kaggle datasets are updated or removed, the "Joint Signal" and "Task-awareness" metrics cannot be verified. The authors must provide a static, immutable archive of the curated data.

Second, the **missing-data handling** is inconsistent and under-specified. The curation pipeline states that rows with missing images are dropped (Appendix A.2), yet the dataset descriptions reveal massive missingness in structured features (e.g., CheXpert has >85% missing for several pathology labels; Glaucoma has >99% missing). The paper does not specify how these missing structured values are encoded (e.g., as NaN, a specific sentinel value, or excluded) during the training of the tabular learners. Since the "Joint Signal" criterion depends on the performance of the structured-only baseline, inconsistent handling of missing values could artificially inflate or deflate the perceived value of the unstructured modalities. The exact data cleaning scripts and schema definitions for missing values must be provided.

Third, the **schema transformation** for regression tasks is opaque. Appendix A.1 states that continuous regression targets are discretized into 20 equal-frequency bins for the TAR finetuning step. This fundamentally changes the data schema from continuous to categorical. The paper must explicitly document the binning strategy (confirming "equal-frequency" vs. "equal-width") and provide the code used to generate these bins. Without this, the "Task-awareness" gain could be an artifact of the discretization process rather than the representation tuning itself.

Finally, the **version control** of the external embedding models (DINO-v3-small, e5-small-v2) is missing. The bibliography lists the models but not the specific commit hashes or version tags. Given the rapid updates to foundation models, the exact weights used to generate the "frozen" and "target-aware" embeddings must be pinned to ensure the results are reproducible.
