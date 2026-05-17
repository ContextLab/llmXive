---
artifact_hash: e5cefeb8f5a622284bf4bd8a2b4800bf995401cb7708f8533b8b272aa0c905d4
artifact_path: projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-17T14:54:55.309394Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

**Data Quality and Provenance Review**

The paper demonstrates strong effort in documenting data sources and annotation pipelines, particularly in Section 4 (`sec:data_pipeline`) and Appendix `sec:appendix_asset_terms`. However, several data quality and provenance issues require clarification before acceptance.

**1. License Consistency and Redistribution Rights**
The Abstract claims SANA-WM is an "open-source world model." However, Table `tab:asset_terms` (Appendix) indicates training data includes SpatialVID-HQ and OmniWorld, both licensed under CC-BY-NC-SA 4.0. Additionally, DL3DV uses "Custom DL3DV project terms." Using Non-Commercial (NC) and ShareAlike (SA) data typically restricts the resulting model's commercial use and may require derivative works to share alike. The paper does not explicitly state the license under which the *model weights* are released. If the model is truly "open-source" (e.g., Apache-2.0 or MIT), this conflicts with the NC-SA data provenance. Please clarify the final model's license and ensure it aligns with the most restrictive training data licenses (Section 4, `sec:data_pipeline`).

**2. Dataset Versioning and Schema**
While Table `tab:data_overview` lists clip counts, it lacks dataset version identifiers (e.g., "DL3DV-10K" vs. "DL3DV-14K"). Citing papers alone (e.g., `dl3dv`) is insufficient for reproducibility if the dataset has been updated. Additionally, the schema for the 213K clips is described via filtering thresholds (Appendix `tab:filter_thresholds`), but the proportion of data dropped due to failed pose estimation (e.g., VIPE/Pi3X failures) is not reported. Knowing the drop rate is critical for assessing selection bias and data quality.

**3. External Link Stability**
The paper relies on external project pages (e.g., `https://nvlabs.github.io/Sana/WM/` in `main.tex`) and GitHub repositories. To prevent link rot, consider archiving these assets via Zenodo or similar services and citing the archive DOI alongside the live URL. The arXiv metadata ID `2605.15178` (May 2026) is inconsistent with current timestamps; please verify this is intentional for the benchmark context, as it affects data provenance tracking.

**4. Missing Data Handling**
Section 4 mentions "80th-percentile inlier filtering" for scale recovery (Appendix `sec:appendix_vipe`), but does not specify how clips with missing intrinsics or poses were handled. Were they imputed, discarded, or masked? Explicitly stating the handling of missing annotations in the main text (Section 4) would improve transparency.

Addressing these points will ensure the data provenance and licensing claims are robust and reproducible.
