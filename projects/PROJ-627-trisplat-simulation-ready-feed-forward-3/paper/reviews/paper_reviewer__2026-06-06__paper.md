---
action_items:
- id: ea8a6e8a6617
  severity: science
  text: Add statistical significance tests (e.g., paired t-tests or confidence intervals)
    to Tables 1-4 to support claimed superiority over baselines.
- id: 4c0def27e24a
  severity: science
  text: Expand the simulation validation section with quantitative metrics from physics
    engines (e.g., collision stability rates, trajectory error) rather than qualitative
    frames.
- id: c748303f4697
  severity: writing
  text: Standardize figure captions, ensure all labels match text references, and
    fix text formatting inconsistencies across sections.
- id: af5d1b753b9d
  severity: writing
  text: 'Verify all bibliography entries have `verification_status: verified` in the
    metadata before final submission.'
artifact_hash: 375d837bf9b63242d32116a8a2f6433796abb291136cadef4ae07e469b227763
artifact_path: projects/PROJ-627-trisplat-simulation-ready-feed-forward-3/paper/metadata.json
backend: dartmouth
feedback: Minor revisions needed for statistical rigor, simulation claim substantiation,
  and formatting consistency.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-06T04:26:13.701354Z'
reviewer_kind: llm
reviewer_name: paper_reviewer
score: 0.0
verdict: minor_revision
---

# Free-form review body

## Strengths
- **Novel Representation:** TriSplat introduces a compelling shift from Gaussian primitives to oriented triangles, directly addressing the "simulation-ready" gap in feed-forward 3D reconstruction.
- **Surface Quality:** Quantitative results on RE10K and DL3DV show consistent improvement in surface metrics (CD, F1) over Gaussian baselines, validating the geometric fidelity claim.
- **Methodological Coherence:** The normal-anchored orientation pipeline and progressive sharpening curriculum are well-motivated and technically sound.
- **Ablation Studies:** The appendix provides detailed ablation on key hyperparameters (blur schedule, opacity temperature), supporting the design choices.

## Concerns
- **Statistical Rigor:** The quantitative tables present mean values without variance or significance testing. Given the high dimensionality of the baselines, statistical significance is required to confirm the observed margins are not due to random seed variance.
- **Simulation Claim Substantiation:** While the "simulation-ready" claim is the paper's core contribution, the simulation evidence (Appendix) relies heavily on qualitative video frames. Physics engine integration should be quantified (e.g., collision stability, dynamic accuracy) to rigorously support the claim.
- **Formatting Consistency:** Minor inconsistencies exist in figure labeling, caption styles, and text formatting (e.g., spacing, citation styles) that detract from the professional polish expected of a final submission.
- **Citation Verification:** Several citations refer to future-dated preprints (2025-2026). Ensure all bibliographic metadata is accurate and verified against the actual archive at submission time.

## Recommendation
This paper presents a strong technical contribution with clear advantages in surface geometry and direct mesh export. The core methodology is sound and the experiments are comprehensive. However, to meet the publication standard for simulation-ready claims, the authors must strengthen the statistical reporting and provide more rigorous quantitative validation of the physics engine integration. These issues are fixable without re-running the full research pipeline. A `minor_revision` verdict is appropriate to allow the authors to address these specific gaps.
