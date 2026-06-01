---
action_items:
- id: 45a1b3e2308d
  severity: science
  text: Explicitly list training dataset names, licenses, and access URLs in a new
    Data Availability section.
- id: 66a770198739
  severity: science
  text: Include version hashes or commit tags for the code and data used to generate
    reported results.
- id: e2683d7e87dc
  severity: writing
  text: Verify all external URLs in the bibliography for stability and provide DOIs
    where possible.
artifact_hash: b208c2b534cdecfcf26735188ae1bff0d6ea19115fa6209ab256b34a9a5cb548
artifact_path: projects/PROJ-638-https-arxiv-org-abs-2605-28820/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-01T14:09:28.284575Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript demonstrates significant ambition in scaling native vision-language models; however, the data quality and provenance reporting require substantial improvement to ensure reproducibility and compliance.

**Data Provenance and Licensing:**
In the **Training Procedure** section (lines 330–365), the authors specify dataset sizes (e.g., "20M large-scale image–text pairs", "60M multimodal samples") but omit critical metadata regarding source identity. Phrases like "collected from diverse web sources" are insufficient for audit purposes. Specific dataset names (e.g., LAION-5B subsets, CommonCrawl snapshots) and their corresponding licenses (e.g., CC-BY, Apache 2.0, proprietary) must be enumerated. The **Ethical Considerations** section (lines 550–560) vaguely states resources are "open-access" but fails to cite specific license terms or compliance mechanisms for data filtering. Without this, the legality and ethical standing of the training corpus cannot be verified.

**Version Control and Reproducibility:**
The paper references a GitHub repository (`https://github.com/EvolvingLMMs-Lab/NEO`) but provides no specific commit hash, release tag, or data version identifier. In the **Implementation Details** (lines 300–320), hyperparameters and hardware are detailed, yet the exact snapshot of the training data pipeline is missing. To enable independent replication, the authors must provide a `data_card` or `datasheet` (following Gebru et al. standards) detailing schema, preprocessing steps, and versioning.

**External Source Stability:**
The bibliography contains numerous URLs (e.g., `https://laion.ai/blog/laion-coco/` in `custom.bib`). These links are susceptible to link rot. The authors should replace unstable URLs with DOIs or archive.org snapshots where available, particularly for benchmark definitions and dataset access points.

**Recommendation:**
These are primarily documentation deficits that can be resolved without re-running experiments. However, they are critical for scientific integrity. Please address these in the revision to meet publication standards for data transparency.
