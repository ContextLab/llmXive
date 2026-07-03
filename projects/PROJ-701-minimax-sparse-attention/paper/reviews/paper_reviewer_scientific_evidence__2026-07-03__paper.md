---
action_items:
- id: 017f85327e66
  severity: science
  text: The claim of 28.4x FLOP reduction and 14.2x/7.6x speedups at 1M context (Abstract,
    Sec 6.3) lacks statistical validation. Provide standard deviations or confidence
    intervals across multiple runs or seeds to rule out variance from hardware noise
    or non-deterministic kernels.
- id: dd51394996b7
  severity: science
  text: The 'Full Attention' baseline in Table 2 (Sec 6.3) is not explicitly defined
    as a model trained with full attention from scratch or a GQA model with full attention.
    If the baseline is a GQA model with full attention, the comparison is valid; if
    it is a different architecture, the claim of 'on par' performance is confounded
    by architectural differences.
- id: 3d008462c744
  severity: science
  text: The ablation study in Table 4 (Appendix) shows mixed results for the 'No-value'
    variant (e.g., +0.9 on MMLU, -1.2 on GSM8K). The conclusion that the value head
    is 'not critical' is weak without a statistical test (e.g., paired t-test) to
    determine if these differences are significant or within noise.
- id: 665b57a106ce
  severity: science
  text: The paper claims the Index Branch 'always includes the local block' (Sec 3.1)
    but the ablation in Table 5 (Appendix) shows 'Removing forced sink/local selection
    has little effect'. This contradicts the stability claim. Clarify if the 'little
    effect' refers to perplexity only or also to long-context retrieval, and provide
    evidence for the stability claim.
artifact_hash: f00725508246b024cf4aa3c534e6f6afc166e2aa03bee30b44dd04e950f05991
artifact_path: projects/PROJ-701-minimax-sparse-attention/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T09:48:58.902454Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling architecture (MSA) with significant efficiency claims, but the scientific evidence supporting the robustness of these claims requires strengthening.

**1. Statistical Rigor and Variance:**
The central claims of massive speedups (14.2x prefill, 7.6x decoding) and FLOP reduction (28.4x) at 1M context (Abstract, Sec 6.3) are presented as single-point measurements. In high-performance computing, especially with custom kernels on H800s, variance due to thermal throttling, memory bandwidth contention, or non-deterministic scheduling can be significant. The manuscript lacks error bars, standard deviations, or confidence intervals. Without multiple runs (e.g., n=5) or a clear explanation of how the measurement was stabilized, it is difficult to rule out that the reported speedups are outliers or artifacts of specific hardware states.

**2. Baseline Definition and Confounding Variables:**
In Table 2 (Sec 6.3), the "Full" column is compared against MSA-PT and MSA-CPT. The text states MSA-PT is "trained from scratch" and MSA-CPT is "continued pretraining from GQA checkpoint." However, it is ambiguous whether the "Full" baseline is a model trained from scratch with full attention or a GQA model with full attention. If the "Full" baseline is a different architecture (e.g., standard Multi-Head Attention vs. GQA), the claim that MSA is "on par" is confounded by the architectural difference between MSA and the baseline. The evidence must explicitly confirm that the "Full" baseline uses the exact same GQA configuration (4 KV heads, 64 Q heads) but with dense attention to isolate the effect of sparsity.

**3. Ablation Interpretation:**
The ablation study in Table 4 (Appendix) regarding the Index Branch value head shows mixed results: the "No-value" variant outperforms "With-value" on MMLU (+0.9) and ARC Challenge (+0.2) but underperforms on GSM8K (-1.2) and MathVista (-1.6). The authors conclude the value head is "not critical" because the differences are "small and benchmark-dependent." However, without statistical significance testing (e.g., paired t-tests across seeds), these differences could be noise. Furthermore, the claim that the value head is "not critical" contradicts the earlier statement that it helps the model "begin sparse training from step zero." The evidence suggests the value head may be critical for *stability* or *specific task types* (math) even if average performance is similar. The conclusion should be nuanced to reflect this task-dependent variance.

**4. Contradictory Stability Claims:**
Section 3.1 states the local block is "always included" to "ensure stability." However, the ablation in Table 5 (Appendix) shows that "Removing forced sink/local selection has little effect on quality." If the forced selection is truly necessary for stability, removing it should degrade performance, particularly in long-context scenarios. The fact that it has "little effect" suggests the model learns to attend to local blocks naturally, rendering the forced mechanism redundant. This contradicts the design rationale and weakens the evidence for the necessity of the forced local block mechanism. The authors should clarify if the "little effect" applies to long-context retrieval (RULER) or only short-context benchmarks.
