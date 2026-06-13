---
action_items:
- id: 4bdb92f3bdf9
  severity: science
  text: Evaluate on additional model architectures (e.g., LLaMA, Mistral) beyond Qwen3
    variants to validate the claim that 'full-attention LLMs are intrinsically sparse'
    is generalizable.
- id: 70a8d7929a1a
  severity: science
  text: Include trainable sparse attention baselines (DSA, NSA) for fair comparison;
    current baselines are mostly training-free, making it unclear if gains come from
    sparsification or additional training.
- id: 52a47142aa4a
  severity: science
  text: Report multiple evaluation runs with confidence intervals on benchmark results
    (LongBench, RULER, AIME) to assess statistical significance of reported improvements.
- id: c4f0d741ce71
  severity: writing
  text: "Clarify speedup measurement methodology: specify hardware configuration,\
    \ batch size, and whether 9.36\xD7 prefill speedup is layer-level or end-to-end\
    \ inference."
- id: 03dc34245075
  severity: science
  text: Provide statistical analysis on head calibration stability across multiple
    documents; appendix shows one heatmap but claims calibration on 'one single sequence'
    is sufficient.
artifact_hash: 2cdfc78b07a5bd64c78a8db6e3f4311cd8e2ebe3c52393699df0143a39308f60
artifact_path: projects/PROJ-617-full-attention-strikes-back-transferring/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-13T07:26:53.180770Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

This paper presents compelling empirical results on sparse attention, but the evidence has several gaps that limit confidence in the central claims.

**Strengths:**
- Comprehensive benchmark coverage (LongBench, RULER, AIME, MMLU-PRO) with 5 baselines
- Detailed ablation studies on retrieval head ratio and low-dimension size (Appendix)
- Training hyperparameters and procedures well-documented (Appendix training section)
- Custom kernel implementation with efficiency analysis

**Evidence Concerns:**

1. **Limited Model Diversity (Lines 240-245):** Only 2 Qwen3 variants evaluated (Qwen3-Coder-30B-A3B, Qwen3-30B-A3B-Think). The central claim that "full-attention LLMs are intrinsically sparse" (Abstract, Introduction) is overgeneralized without testing on LLaMA, Mistral, or other architectures. Head specialization patterns may be model-specific.

2. **Missing Trainable Baselines (Lines 260-270):** Comparisons are against mostly training-free methods (RazorAttn, Minference, SnapKV). Trainable sparse attention methods like DSA and NSA are mentioned in Related Work but not evaluated. This makes it unclear whether performance gains stem from the sparsification mechanism or simply from additional training (Stage 2 uses 180M tokens).

3. **Statistical Significance (Lines 310-350):** All benchmark results appear to be single-run. No confidence intervals, p-values, or variance across multiple runs reported. The LongBench result showing top-p (54.24) > Full Attn (53.80) is suspicious and needs verification against statistical noise.

4. **Speedup Measurement (Lines 375-385):** The 9.36× prefill speedup at 1M context lacks measurement details. Is this single-layer, single-head, or end-to-end? What batch size, GPU memory configuration, and kernel fusion level? Without this, reproducibility is compromised.

5. **Head Calibration Claim (Lines 190-200, Appendix):** The claim that "running this calibration on just one single long text sequence is sufficient" (Section 3.1) is supported by one heatmap in Appendix (Fig. appd:headwise_attnmap) but lacks statistical validation across multiple documents. The appendix shows head scores are stable, but variance analysis is missing.

6. **Training Data Overlap Risk:** Stage 1 uses FineWeb, Stage 2 uses Dolma 3 Longmimo Mix. LongBench and RULER contain synthetic/curated data that could overlap with these training corpora, potentially inflating accuracy results.

**Recommendations:**
- Add experiments on 1-2 additional model families to validate generalizability
- Include at least one trainable baseline (DSA or NSA) for fair comparison
- Report benchmark results with ≥3 runs and confidence intervals
- Add a measurement appendix with detailed speedup methodology
- Quantify head calibration stability with variance across multiple calibration documents

The core method appears sound, but these evidence gaps must be addressed before the broad claims about "intrinsic sparsity" can be fully supported.
