---
action_items:
- id: f34e06331008
  severity: science
  text: Resolve the 30x discrepancy between the claimed 302k hours (Abstract/Intro)
    and the ~9.7k hours sum in Appendix D Table. Audio stitching cannot increase total
    duration.
- id: 35bcd81b69de
  severity: fatal
  text: Clarify the license for StreamAudio-2M and confirm redistribution rights for
    ElevenLabs/AudioX generated content, as commercial APIs often restrict public
    dataset release.
- id: e5a6c37ffbd5
  severity: writing
  text: Provide a specific dataset version tag or content hash for the HuggingFace
    repository to ensure reproducibility of the exact training data used.
artifact_hash: d722b827ffcc42ef33cad3308518a181a01c5d135cbbac51efaf0289e64033d0
artifact_path: projects/PROJ-666-https-arxiv-org-abs-2606-05121/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-12T11:00:16.086089Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: full_revision
---

The manuscript introduces `StreamAudio-2M` as a primary contribution, yet critical data quality issues regarding provenance, statistics, and licensing undermine its validity and reproducibility.

First, there is a severe inconsistency in dataset scale reporting. The Abstract and Introduction state the corpus comprises `302k hours` of audio (lines 105, 145). Conversely, Appendix D (Table `tab:app:sources`) itemizes source durations summing to approximately `9,725 hours`. Since audio stitching and synthesis do not create duration from nothing, this 30-fold discrepancy indicates a factual error in the main claims or the appendix table. This must be corrected to ensure the dataset size matches the reported benchmarks and training compute claims.

Second, data provenance and licensing are unclear. The construction pipeline relies on `ElevenLabs` and `AudioX` for synthesized clips (Section 4.1, Appendix D). `ElevenLabs` is a commercial service with Terms of Service that often prohibit redistribution of generated content in public datasets. Furthermore, the license for `StreamAudio-2M` itself is not specified in the manuscript. Without explicit licensing that covers all source materials (including `MOSS`, `AudioSet`, and commercial APIs), the dataset's public release may be legally non-compliant, potentially invalidating the data contribution.

Third, version control is insufficient. The HuggingFace repository link (line 55) does not specify a version tag or content hash. For reproducibility, a specific dataset version (e.g., `v1.0`) and a content hash should be provided to ensure reviewers and future users can access the exact data used for training.

Addressing these data quality concerns is essential before the data contribution can be trusted or the paper accepted.
