---
artifact_hash: afa8fa72a7934c7df53d880056c75fcf5c3f630f18439721edf2b52c416ec85b
artifact_path: projects/PROJ-565-edit-compass-editreward-compass-a-unifie/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-17T14:50:37.271307Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

**Data Quality and Provenance Review**

The manuscript provides a detailed narrative of data construction in the Appendix (\bench Data Construction, lines ~1330-1450), but several critical data quality documentation elements require clarification to ensure reproducibility and legal compliance.

**1. License Specificity:** In Appendix `\bench Data Construction` (Section "General and Complex tasks"), the authors state that images were collected from Unsplash, Pexels, Pixabay, and Freepik "under permissive licenses." This is insufficient for a public benchmark. You must specify the exact license type (e.g., CC-BY-4.0, CC0, or platform-specific terms) for each source. Different platforms have distinct requirements for attribution and commercial use. Without explicit license identifiers, downstream users cannot guarantee compliance when redistributing or fine-tuning on this data.

**2. API Dependency and Reproducibility:** The data construction pipeline relies heavily on proprietary APIs (Gemini 3 Pro, GPT-5.1) to generate editing instructions (lines ~1360-1370). This introduces a significant reproducibility risk; if API access changes or models are updated, the dataset generation process becomes non-deterministic or inaccessible. For a benchmark claiming "human-aligned" quality, consider archiving the exact prompt versions and model outputs used, or provide a fallback using open-weight models to ensure long-term accessibility of the data generation logic.

**3. Version Control and Schema:** While a GitHub repository is listed on the title page, there is no explicit version tag (e.g., v1.0) linked to this specific paper submission. Additionally, while evaluation prompts are provided (e.g., JSON output structures in Appendix), a formal dataset schema (defining fields like `instruction`, `source_image_path`, `target_image_path`, `metadata`) is not explicitly documented. Including a `schema.json` or README table defining the data structure is necessary for automated ingestion by the community.

**4. External Link Stability:** The paper cites numerous external benchmarks and models. Ensure that all URLs in the bibliography (e.g., arXiv links, GitHub repos) are checked for stability. Given the rapid evolution of image editing models, "link rot" is a high risk for the cited baselines. Recommend using persistent identifiers (DOIs) or archiving model weights where possible.

To achieve `accept`, please revise the Appendix to include specific license metadata for source images, document the API versions used for data generation, and provide a clear data schema definition.
