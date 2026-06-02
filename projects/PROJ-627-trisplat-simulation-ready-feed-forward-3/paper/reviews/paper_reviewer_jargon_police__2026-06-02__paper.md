---
action_items:
- id: df499ee257ad
  severity: writing
  text: Define acronyms TSDF, SE(3), SO(3), and LPIPS at first use in the main text
    to ensure accessibility for non-specialist readers.
- id: c599385ccc89
  severity: writing
  text: Replace dense jargon terms like 'post-hoc', 'gauge ambiguity', and 'latent
    variable' with plainer alternatives (e.g., 'subsequent', 'coordinate ambiguity',
    'internal representation').
artifact_hash: 375d837bf9b63242d32116a8a2f6433796abb291136cadef4ae07e469b227763
artifact_path: projects/PROJ-627-trisplat-simulation-ready-feed-forward-3/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-02T07:54:32.884186Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript presents a strong technical contribution, but the density of specialized terminology may hinder accessibility for readers outside the immediate 3D vision community. Several acronyms appear without definition at their first occurrence, which violates standard academic writing conventions for broader readability. Specifically, 'TSDF' is used in the Introduction (`sections/01_introduction.tex`) to describe mesh extraction methods, but 'Truncated Signed Distance Function' is never spelled out. Similarly, 'SE(3)' and 'SO(3)' are used in the Method section (`sections/03_method.tex`) to describe camera poses and rotations without defining them as the Special Euclidean and Special Orthogonal groups. 'LPIPS' appears in `sections/03_method.tex` under Training Objectives without the full name 'Learned Perceptual Image Patch Similarity'.

Beyond acronyms, certain phrases rely on insider shorthand that could be simplified. The term 'post-hoc' (Abstract, Introduction) is common but 'subsequent' or 'after-the-fact' is clearer for non-specialists. 'Gauge ambiguity' (`sections/03_method.tex`) is a technical concept that could be phrased as 'coordinate system ambiguity' for broader clarity. 'Latent variable' (`sections/03_method.tex`) could be 'internal representation'. 'Feed-forward' is used repeatedly; while standard, 'single-pass' might be more descriptive of the inference speed benefit. 'Gauge ambiguity' and 'latent variable' appear in contexts where simpler language would not lose technical precision but would improve readability.

Additionally, 'SH' is used in the Appendix (`sections/07_appendix.tex`) for spherical harmonics without explicit acronym definition, though the phrase is present earlier. 'PhysX' (`sections/07_appendix.tex`) is a proprietary backend name; ensuring the context clarifies it as a physics engine is helpful.

To improve the paper's reach, I recommend a pass to define all acronyms upon first mention and to simplify high-density jargon where synonyms exist without sacrificing precision. This will align the paper with broader accessibility standards while maintaining technical rigor. These changes are purely editorial and do not require re-running experiments, making them straightforward to address before final publication.
