---
action_items: []
artifact_hash: 0af0fa627d69c39f9437c6e8b879903d02afc89b298d92518865da3572e8baac
artifact_path: projects/PROJ-1013-vision-as-unified-multimodal-generation/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-09T02:58:56.119245Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.5
verdict: accept
---

The paper presents a large-scale computer vision model trained on a corpus constructed from public datasets and generated annotations. A review of the data construction section (Section 3) and the appendix reveals that the authors explicitly state the corpus is built from "public images" and "available public annotations" (Section 3.2). The released artifact, SN-VC-50M, is described as containing "generated and curated targets" and "source lists, prompt templates, conversion rules," while explicitly noting that "raw RGB images from public datasets" are not redistributed to avoid licensing issues (Appendix, SN-VC-50M Release Summary).

The paper does not appear to use private human-subjects data, PII, or data scraped in violation of Terms of Service. The datasets listed in the appendix (e.g., COCO, OpenImages, Cityscapes, ScanNet) are standard public benchmarks with established licenses for research use. The use of synthetic data generation tools (e.g., MoGe-2, LingBot-Depth) to create dense labels from sparse or missing annotations is a standard practice in the field and does not introduce new ethical risks regarding consent or privacy, provided the source images are public, which the authors assert.

There is no evidence of dual-use capabilities described in a manner that lowers the barrier to specific harms (e.g., automated surveillance of individuals, generation of deceptive media for disinformation) without mitigation. The model's capabilities (detection, segmentation, depth estimation) are standard computer vision tasks. The paper does not disclose any operational vulnerabilities in live systems, nor does it involve human subjects requiring IRB approval.

Consequently, no specific safety or ethics risks requiring mitigation or disclosure were identified. The paper adheres to standard norms for data provenance and release in the computer vision community.
