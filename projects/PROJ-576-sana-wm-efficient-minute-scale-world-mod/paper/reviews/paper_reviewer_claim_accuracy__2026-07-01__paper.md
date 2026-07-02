---
action_items:
- id: f49c66039550
  severity: writing
  text: 'The review focuses on the factual accuracy of claims and their supporting
    evidence within the provided manuscript. Hardware and Performance Claims The most
    critical factual issue lies in the Abstract and Introduction, where the authors
    claim: "its distilled variant can be deployed on a single RTX 5090 with NVFP4
    quantization to denoise a 60s 720p clip in 34s." As of the current date, the NVIDIA
    RTX 5090 is not a released product, nor are its specifications or performance
    benchmarks publicly avai'
artifact_hash: e5cefeb8f5a622284bf4bd8a2b4800bf995401cb7708f8533b8b272aa0c905d4
artifact_path: projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:43:57.835390Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses on the factual accuracy of claims and their supporting evidence within the provided manuscript.

**Hardware and Performance Claims**
The most critical factual issue lies in the Abstract and Introduction, where the authors claim: "its distilled variant can be deployed on a single RTX 5090 with NVFP4 quantization to denoise a 60s 720p clip in 34s." As of the current date, the NVIDIA RTX 5090 is not a released product, nor are its specifications or performance benchmarks publicly available. Citing a non-existent hardware platform as the basis for a specific empirical performance metric (34s latency) renders this claim factually incorrect and unverifiable. This must be corrected to reference a currently available GPU (e.g., RTX 4090) or explicitly framed as a theoretical projection based on architectural scaling, rather than a measured result.

**Throughput Comparisons**
The Abstract states the model achieves "36x higher throughput" than prior baselines. While Table 1 (main_table.tex) provides efficiency metrics, the comparison is not strictly "apples-to-apples." The baselines (e.g., LingBot-World, HY-WorldPlay) are listed as running on 8 GPUs, whereas SANA-WM is evaluated on 1 GPU. The 36x figure appears to conflate the efficiency gain from the architecture with the massive reduction in hardware footprint (8 GPUs vs 1). Without normalizing for the number of GPUs or explicitly stating that the comparison is "single-GPU throughput vs. multi-GPU baseline throughput," the claim of "36x higher throughput" is ambiguous and potentially misleading regarding the algorithmic efficiency alone.

**Data Composition**
The Abstract and Introduction claim the model is trained on "~213K public video clips." However, Table 2 (tables/train-data.tex) reveals that the dataset includes 14,881 synthetic clips from "DL3DV GS Refined" and 1,720 from "OmniWorld" (synthetic/game data). While these are public sources, the term "public video clips" typically implies real-world footage. The synthetic portion constitutes roughly 7.8% of the total data. While not a fatal error, the claim should be refined to "public and synthetic video clips" or "publicly available data sources" to accurately reflect the data composition described in the data pipeline section.

**Citation Support**
The citations for the baselines (LingBot-World, HY-WorldPlay) and the specific metrics (VBench, Pi3X) appear consistent with the text. The claim regarding the "Robust Annotation Pipeline" using VIPE, Pi3X, and MoGe-2 is well-supported by the detailed description in Section 4 and the Appendix. The mathematical derivations for the GDN key scaling (Eq. 4-6) are internally consistent with the stated goal of preventing state explosion.

In summary, the paper makes strong claims about efficiency and performance, but the reliance on unreleased hardware for a specific latency number and the conflation of hardware count with algorithmic throughput in the efficiency claim require correction to meet factual accuracy standards.
