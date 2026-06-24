---
action_items:
- id: 7dbeaaa11bd1
  severity: writing
  text: "Add a clear data availability and licensing statement for ImageNet, including\
    \ the exact version (e.g., ImageNet\u20111K 2023 release) and the permissive or\
    \ restrictive license under which the data is used."
- id: ce98912f6bf6
  severity: writing
  text: "Provide persistent, archived URLs (e.g., Zenodo or Internet Archive) for\
    \ any external resources referenced in the paper (e.g., code repositories, pretrained\
    \ checkpoints, or third\u2011party datasets) to mitigate link rot."
- id: 9b8597adfae6
  severity: writing
  text: Document the full preprocessing pipeline (e.g., resizing, normalization, augmentation)
    and the schema of the input tensors (shape, datatype, range) so that future reproductions
    can verify data handling.
- id: ed03f820c7e4
  severity: writing
  text: "Include checksums (e.g., SHA\u2011256) for the exact dataset files used during\
    \ training to enable verification of data integrity."
- id: 08b15557cff3
  severity: writing
  text: "If any custom data splits or subsets are employed (e.g., validation split\
    \ for early\u2011stop experiments), describe how they were generated and provide\
    \ the split files or a deterministic script."
artifact_hash: 7a4bc7e64a39662319f7490ada4c2be57d6c20dd18ca5f1225c2e0b697bf14b3
artifact_path: projects/PROJ-625-https-arxiv-org-abs-2605-20708/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-24T18:01:15.993302Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

**Data‑Quality Review (200‑500 words)**  

The manuscript presents a novel routing mechanism for Diffusion Transformers (DiTs) and evaluates it on ImageNet 1K at 256 × 256 resolution. From a data‑quality perspective, the paper lacks several essential provenance and reproducibility details. First, the use of ImageNet is mentioned only in passing (“we train on ImageNet‑1K”) without specifying the exact release (e.g., 2012, 2023) or the licensing terms under which the authors accessed the data. Because ImageNet’s license is non‑commercial and requires attribution, an explicit statement is required to confirm compliance and to inform readers of any usage restrictions.  

Second, the preprocessing pipeline is described as “the same as SiT” (Section 4.1) but the SiT recipe is not reproduced in the paper nor linked to a stable, archived source. This omission makes it difficult to verify that the same data transformations (e.g., random cropping, color jitter, RMSNorm) were applied, which is crucial for interpreting the reported FID improvements. A concise schema—detailing input tensor shape, datatype (e.g., float16), value range, and any normalization—should be added to the methods section or an appendix.  

Third, the paper does not provide any checksums or version identifiers for the dataset files used. Including SHA‑256 hashes for the training and validation splits would enable future researchers to confirm that they are using identical data, especially when ImageNet is redistributed across mirrors that may differ subtly.  

Fourth, all external resources (e.g., the codebase for DAR, pretrained checkpoints, the SiT baseline) are referenced only by name. No persistent URLs or archival links are supplied, raising the risk of link rot. The authors should deposit code and model artifacts in a long‑term repository (e.g., Zenodo, Figshare) and cite the DOI.  

Finally, the paper does not discuss any missing‑data handling or data‑quality checks (e.g., filtering corrupted images). While ImageNet is generally clean, a brief statement confirming that no additional filtering was performed would close this gap.  

Addressing these points will substantially improve the paper’s data provenance, licensing clarity, and reproducibility, aligning it with community standards for high‑quality generative‑model research.
