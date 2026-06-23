---
action_items:
- id: aa9b5b3f5747
  severity: science
  text: "Add a clear data availability statement that lists all external datasets\
    \ used (ImgEdit, Sudoku synthetic generation code, MATH, MBPP, ARC\u2011Challenge)\
    \ with their licenses, download URLs, and version identifiers (e.g., DOI or commit\
    \ hash)."
- id: 4ef8ba1f7b80
  severity: science
  text: "Provide a persistent archive (e.g., Zenodo or OSF) for the training data\
    \ splits and any synthetic data generation scripts, and include checksums (SHA\u2011\
    256) for each file to enable verification."
- id: 01f874923740
  severity: writing
  text: "Document the exact preprocessing steps applied to each dataset (tokenization,\
    \ corruption distribution \u03BD, top\u2011k selection) and include the corresponding\
    \ configuration files in the repository."
- id: fa53888aa1be
  severity: writing
  text: Ensure that all external resources referenced in the paper (figures, tables,
    code snippets) have stable URLs; consider mirroring PDFs and images in the same
    archive to avoid link rot.
- id: 345a1243cccc
  severity: science
  text: "Specify the software versioning used for the base models (Lumina\u2011DiMOO,\
    \ LLaDA, etc.) and the frozen checkpoint \u03B8\u2080 employed for the top\u2011\
    k corruption distribution, including repository tags or commit hashes."
- id: 7a73281f0cc6
  severity: writing
  text: If any dataset is not publicly releasable due to licensing restrictions, describe
    the access procedure (e.g., request form) and provide a statement confirming compliance
    with the original license.
artifact_hash: 7fece54febe808e7b8d966174edf071d45cfb2bebbcbdcb010a99fdaf0b84671
artifact_path: projects/PROJ-765-multi-turn-reflective-masking-elicits-re/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-23T10:22:50.976060Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript focuses on a novel post‑training paradigm for Mask Diffusion Models (MDMs) but provides insufficient information to assess the reproducibility and integrity of the underlying data assets. While the experiments cite several external datasets (ImgEdit [Ye 2025], Sudoku synthetic boards, MATH [Hendrycks 2021], MBPP [Austin 2021], ARC‑Challenge [Clark 2018]), the paper does not disclose their licenses, exact versions, or download locations. This omission makes it impossible for reviewers or future researchers to verify that the data comply with the stated usage policies or to obtain identical splits for replication.

The synthetic trajectory generation described in §4.3 and Appendix A relies on a “corruption distribution ν” and a “top‑k proposal from a frozen checkpoint θ₀”. However, the checkpoint source, its version tag, and the exact hyper‑parameters (e.g., k = 50) are not recorded. Without these details, the stochastic data generation pipeline cannot be reproduced, and the reported theoretical guarantees (Theorem 1, 2) cannot be empirically validated.

Figures and tables are referenced via PDF files stored in the repository (e.g., `figures/Image_main_paper.pdf`). No persistent identifiers (DOI, archive URL) are provided, raising the risk of link rot. Moreover, the codebase used for training (the `dLLM` library, the custom `init.tex` macros, and the training scripts) is not linked to a version‑controlled repository, nor are the exact library versions (e.g., PyTorch, CUDA) listed.

To bring the work up to community standards for data quality, the authors should add a comprehensive data statement that enumerates each dataset, its license (e.g., CC‑BY‑4.0 for ImgEdit), and a stable download link. They should archive the exact training splits and any synthetic data generation scripts on a long‑term platform (Zenodo, OSF) and provide SHA‑256 checksums. All software dependencies, including the base MDM checkpoints and the `dLLM` version, should be pinned to specific commit hashes or release tags. Finally, ensuring that all figure assets are stored alongside the paper in the same archive will mitigate future link‑rot issues. Addressing these points will substantially improve the paper’s reproducibility and data provenance.
