---
action_items:
- id: 3d833baf343e
  severity: writing
  text: Define all acronyms at first use, especially in the Abstract (e.g., NVFP4,
    VAE, LoRA, GEMM, W4A4, KV cache).
- id: 5324790d7556
  severity: writing
  text: Reduce jargon density in the Abstract; explain 'Balanced SP' and 'loss-bearing
    tokens' in plain English.
- id: 04d3bbd33a5a
  severity: writing
  text: Define informal abbreviations like 'OOM' (Table 1) and framework-specific
    terms like 'FSDP', 'EMA', 'RoPE' in the Appendix.
artifact_hash: 6191ec14b8389b89c96572533c3f6f5e9333a3f73e89fe363432c3a9d7429fb8
artifact_path: projects/PROJ-604-https-arxiv-org-abs-2605-18739/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-04T19:12:34.031049Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The Abstract introduces a high density of acronyms and technical terms without immediate definition, creating a significant barrier for non-specialist readers. Specifically, `NVFP4`, `VAE`, `LoRA`, `GEMM`, `W4A4`, and `KV cache` appear in the Abstract (lines 1-25) but are not defined until Section 2.2 (line ~250), Section 3.3 (line ~320), or not at all. For example, "NVFP4" is the core contribution but lacks a plain-language expansion (e.g., "NVIDIA 4-bit Floating Point") in the Abstract. Similarly, "VAE" is used in line 14 of the Abstract before its first definition in Section 3.3.

The term "Balanced SP" (Abstract, line 10) is introduced as an instantiation of "sequence-parallel" without explaining what makes it "balanced" in plain English. Phrases like "loss-bearing tokens" (Abstract, line 12) and "communication-native order" (Section 2.1, line 165) rely heavily on internal system jargon that obscures the underlying mechanism for general audiences.

In the Appendix, acronyms such as `FSDP` (Appendix A.3), `EMA` (Appendix A.3), `RoPE` (Appendix A.2), and `QAT` (Appendix A.1) are used without expansion, assuming reader familiarity with specific deep learning frameworks. `OOM` in Table 1 (line 350) is an informal abbreviation that should be defined as "Out of Memory".

To improve accessibility, please expand all acronyms at their first occurrence, particularly in the Abstract and Introduction. Replace dense jargon phrases with clearer descriptions where possible (e.g., explain "Balanced SP" as "a sequence parallelism strategy that balances workload across GPUs"). Define hardware-specific terms like "Blackwell GPUs" briefly for context. Ensure that terms like "sink-token sliding windows" (Section 3.2) are explained in simple terms before being used in equations. This will ensure the paper's infrastructure contributions are understood beyond the specialized systems community.
