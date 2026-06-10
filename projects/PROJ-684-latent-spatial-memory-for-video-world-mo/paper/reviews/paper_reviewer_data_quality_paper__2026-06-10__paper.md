---
action_items:
- id: caa3598ef1fc
  severity: writing
  text: Dataset license for RealEstate10K and WorldScore benchmark is not specified.
    Add explicit license terms for all training/evaluation data to ensure legal compliance
    and reproducibility (Section 4.1, lines 1-30).
- id: 51b3dc34a51d
  severity: writing
  text: No code repository URL or version control information (Git tags, commit hashes)
    is provided. Add a stable code release link with versioning to support reproducibility
    (Section 4.1 or Appendix).
- id: f2221eb35f83
  severity: writing
  text: The aka.ms project page link is a short URL that may suffer from link rot.
    Provide a permanent archive link (e.g., Zenodo DOI, GitHub) for project resources.
- id: 24434bc8e5a2
  severity: writing
  text: Data schema for the latent spatial memory cache (Eq. 2-4) lacks formal documentation.
    Specify file formats, coordinate conventions, and data types for any released
    cache artifacts.
- id: ab4d4e63f46d
  severity: writing
  text: Missing data handling policies (dynamic object filtering, sky exclusion) are
    described but lack quantitative thresholds. Document data quality criteria and
    filtering thresholds used in cache construction.
artifact_hash: bd887508a66694d64c816f18d1aa2ba986169658581dbcff682b0dc9431540b8
artifact_path: projects/PROJ-684-latent-spatial-memory-for-video-world-mo/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-10T19:08:01.225770Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The paper makes several claims about data usage and efficiency but lacks comprehensive data quality documentation required for reproducibility and legal compliance.

## Data Provenance & Licensing (Critical)

Section 4.1 states training uses RealEstate10K and evaluation uses WorldScore benchmark, but no license terms are provided for either dataset. RealEstate10K has specific usage restrictions that must be acknowledged. The WorldScore benchmark itself lacks license documentation in the bibliography. Without explicit licensing information, downstream users cannot legally reproduce or build upon this work.

## Version Control & Reproducibility

No Git repository URL, commit hashes, or data version identifiers are provided. The project page link (aka.ms/latent-spatial-memory) is a short URL susceptible to link rot. For a 2026-dated paper with significant efficiency claims, permanent archival links (Zenodo DOI, GitHub releases) are essential for scientific integrity.

## Data Schema Documentation

The latent memory structure (Eqs. 2-4, Appendix) describes the mathematical representation but lacks formal schema documentation. If cache artifacts are released, file formats, coordinate systems (world vs. camera space), and data type specifications must be documented for external use.

## Missing Data Handling

Dynamic object filtering and sky exclusion are described qualitatively (Section 3.3, Eq. 6) but lack quantitative quality thresholds. What confidence scores trigger exclusion? What percentage of cache cells are typically masked? These parameters affect reproducibility.

## External Link Stability

The bibliography contains multiple 2025-2026 dated citations (DepthAnything 3, WorldScore, Spatia, etc.). While some may be preprints, the density of future-dated references raises concerns about citation verifiability. Ensure all external resources have stable, verifiable URLs.

These issues do not invalidate the scientific contribution but prevent full reproducibility and legal compliance.
