---
action_items:
- id: 9f9670e4cd00
  severity: writing
  text: "Add an explicit data availability and licensing statement for all external\
    \ datasets used (Places2, CelebA\u2011HQ, FFHQ, LVIS, DeepFakeFace), including\
    \ version numbers and source URLs."
- id: dbfcc7173339
  severity: writing
  text: "Provide a public code repository (e.g., GitHub) for Moebius with a clear\
    \ open\u2011source license, and reference the exact commit/tag used for the reported\
    \ experiments."
- id: 435af6447f4b
  severity: writing
  text: Document the provenance and version of the teacher model (PixelHacker) and
    any other pretrained components (VAE, LCG embeddings), including links to the
    exact releases.
- id: a9989b2878b5
  severity: writing
  text: Archive all external URLs (project page, dataset links, pretrained model links)
    using a service like archive.org or provide DOIs to mitigate link rot.
- id: 946a986c3acf
  severity: writing
  text: Specify the data preprocessing pipeline (mask generation, train/val splits)
    in a reproducible schema (e.g., JSON/YAML) and include it as supplementary material.
artifact_hash: 1d1f309ade55ca62f397b416937bcdd4ef70b4bedba292a5117896884d675799
artifact_path: projects/PROJ-751-moebius-0-2b-lightweight-image-inpaintin/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-25T00:15:47.538983Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript focuses on a novel lightweight diffusion architecture for image inpainting, but from a data‑quality perspective several critical omissions limit reproducibility and long‑term verifiability.

1. **Dataset provenance and licensing** – The paper repeatedly references public datasets (Places2, CelebA‑HQ, FFHQ, LVIS, DeepFakeFace) without stating their licenses, version numbers, or exact download URLs. This makes it impossible for reviewers or future readers to confirm that the same data were used, especially given that many of these datasets have multiple releases with differing terms. An explicit data‑availability section should list each dataset, its version (e.g., “Places2 train split, 1.8 M images, version 2023‑01”), and the corresponding license (e.g., CC‑BY‑4.0).

2. **Missing code and model version control** – No code repository is provided, nor is there any reference to a commit hash or tag for the Moebius implementation. The paper also relies on a teacher model (PixelHacker) and a VAE encoder (SDXL VAE) but does not give the exact model checkpoints or their version identifiers. Without a public repository and versioned releases, the community cannot verify the reported parameter counts, FLOPs, or latency measurements.

3. **External link stability** – The project page URL (https://hustvl.github.io/Moebius) and several arXiv references are the only persistent links. Other URLs (e.g., to the Muon optimizer, E‑LatentLPIPS, commercial edit systems) are not archived, risking link rot. Providing archived copies or DOIs would safeguard the paper’s reproducibility.

4. **Schema for preprocessing and masks** – The experimental setup mentions mask percentages (40–50 % for Places2, “large/small” masks) but does not provide a machine‑readable description of how masks are generated. Supplying a JSON/YAML schema (including random seed, mask generation algorithm, and any post‑processing steps) would greatly aid replication.

5. **Citation of pretrained components** – While the paper cites the PixelHacker paper, it does not include a direct link to the exact pretrained weights used for distillation, nor does it state whether those weights are under a permissive license. Clarifying this is essential for legal reuse and for reproducing the adaptive multi‑granularity distillation pipeline.

Addressing these points will bring the manuscript in line with best practices for data provenance, licensing, and reproducibility, ensuring that the impressive engineering contributions can be reliably built upon by the community.
