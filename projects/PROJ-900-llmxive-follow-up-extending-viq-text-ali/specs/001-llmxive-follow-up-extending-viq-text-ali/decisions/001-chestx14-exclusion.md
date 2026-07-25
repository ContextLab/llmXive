# Decision Record 001: Exclusion of ChestX-ray14 Dataset

## Status
Accepted

## Context
The original project specification (FR-003) and User Story 2 (US-2) identified the ChestX-ray14 dataset as a primary source for evaluating high-resolution visual reconstruction fidelity in medical imaging contexts. The hypothesis was that the ViQ (Visual Quantized) representations would maintain semantic alignment and resolution invariance even on domain-specific medical data.

However, during the execution of the foundational phase (T005 and subsequent data loading tests), the following issues were identified:
1. **Lack of Verified Source**: The original download URLs for ChestX-ray14 (hosted by NIH) have been unstable or deprecated in the CI environment. No stable, programmatic mirror exists that guarantees bit-for-bit reproducibility without manual intervention.
2. **CI Compatibility Risks**: The dataset size (~10GB uncompressed) and specific file structure (nested directories with specific naming conventions) caused frequent failures in the automated pipeline, particularly when running on ephemeral CI runners with limited ephemeral storage.
3. **Verification Failure**: Attempts to fetch the dataset via `datasets` library or direct HTTP requests resulted in intermittent timeouts and checksum mismatches, violating Constitution Principle III (Data Hygiene) which requires verified integrity before processing.

## Decision
The project team has decided to **exclude** the ChestX-ray14 dataset from the scope of this research iteration (PROJ-900).

Consequently:
- Requirement FR-003 (Dataset Inclusion) is amended to remove ChestX-ray14.
- User Story 2 (US-2) is amended to focus exclusively on ImageNet-1K and COCO datasets for high-resolution fidelity evaluation.
- The hypothesis regarding "resolution invariance on medical imaging" is deferred to a future iteration once a verified, stable source for medical imaging data is established.

## Consequences
### Positive
- **Stability**: The automated pipeline (quickstart.md) can now run reliably on standard CI environments without manual data intervention.
- **Reproducibility**: All remaining data sources (COCO, ImageNet-1K) are available via stable Hugging Face Datasets endpoints with guaranteed checksums.
- **Focus**: The research scope is narrowed to natural images, allowing for deeper analysis of texture complexity and semantic alignment on the remaining datasets.

### Negative
- **Domain Gap**: The initial validation of ViQ invariance is limited to natural images. Generalization to medical imaging remains an open question for future work.
- **Reduced Scope**: The original ambition of a cross-domain evaluation is not met in this iteration.

### Mitigation
- Future iterations will explicitly track the acquisition of a verified medical imaging dataset (e.g., via MIMIC-CXR or a stable NIH mirror) as a prerequisite for re-introducing this requirement.
- The exclusion is documented in the `README.md` and `quickstart.md` to ensure transparency for reviewers.

## References
- Original Spec: `/specs/001-viq-resolution-invariance/spec.md` (FR-003, US-2)
- Related Task: T005 (Data Loader implementation)
- Related Task: T036 (Spec Alignment)
- Related Task: T036b (Decision Record: Native Ground Truth)