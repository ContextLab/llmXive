---
action_items:
- id: 7b78c5a78156
  severity: science
  text: The claim that Mellum2 'matches Qwen2.5-7B throughput on H100' (Sec 1) and
    'matches sync latency' (Sec 6) is over-claimed without explicit hardware configuration
    details (e.g., batch size, sequence length, precision mode) in the text. The throughput
    figure (20.2 req/s) is highly sensitive to these parameters; without them, the
    comparison is not reproducible or verifiable.
- id: 384311f5e06b
  severity: writing
  text: "The statement that the model is 'competitive with 4B\u201314B open baselines\
    \ at 2.5B dense compute' (Abstract) over-extrapolates the results. While it matches\
    \ Qwen2.5-7B in throughput, the pre-training evaluation (Table 1) shows it underperforming\
    \ Qwen2.5-7B on HumanEval (41.5% vs 55.5%) and MMLU (70.9% vs 71.8%). The 'competitive'\
    \ claim requires qualification regarding the specific trade-off between speed\
    \ and accuracy."
- id: 09b2823191bb
  severity: science
  text: The assertion that 'Muon + FP8 recipe' enabled 'Stable training at 10T tokens'
    (Sec 1) is a causal claim not fully supported by the provided ablation data. The
    paper mentions Muon and FP8 but does not present a controlled ablation isolating
    these factors from the MoE architecture or data curriculum to prove they were
    the sole or primary drivers of stability at that scale.
- id: 8ac89decb25e
  severity: writing
  text: The claim that 'Layer-selective YaRN... outperforms uniform RoPE base' (Sec
    3) is supported by RULER scores, but the text admits 'Absolute scores are conservative
    due to a prompt-formatting issue' (Sec 3). The paper should explicitly state that
    the *relative* improvement is the valid finding, rather than implying the absolute
    performance is fully realized, to avoid over-claiming the model's actual long-context
    capability.
artifact_hash: cb4466a31e7b640ad51d8c2f8310c27b9827d874fc645a40e58bc959301ab98e
artifact_path: projects/PROJ-647-mellum2-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T15:30:54.627626Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding efficiency and performance that slightly overreach the provided evidence or lack necessary context for verification.

First, the efficiency claims in the Introduction and Section 6 are the most vulnerable to over-interpretation. The authors state the model "matches Qwen2.5-7B throughput on H100" and achieves "21% higher throughput" (20.2 req/s vs 16.7 req/s). However, the text does not specify the batch size, sequence length, or specific vLLM configuration used to generate these numbers. Throughput is a function of these variables; without them, the claim that the architecture *inherently* matches the baseline is not fully substantiated. The comparison could be an artifact of a specific, non-standard inference setup rather than a general architectural advantage.

Second, the Abstract and Introduction claim the model is "competitive with 4B–14B open baselines at 2.5B dense compute." While the throughput data supports the "2.5B compute" aspect, the performance data in Table 1 (Pre-training evaluation) shows the model lagging behind Qwen2.5-7B on key benchmarks like HumanEval (41.5% vs 55.5%) and MMLU (70.9% vs 71.8%). The term "competitive" is used loosely here; the model is faster but less accurate on these specific tasks. The paper should qualify this claim to reflect the specific trade-off (speed vs. accuracy) rather than implying a general equivalence in capability.

Third, the causal attribution of training stability to the "Muon + FP8 recipe" (Abstract, Section 1) is an over-extrapolation. While the paper details the use of these techniques, it does not provide an ablation study isolating their effect from the MoE architecture or the data curriculum. Attributing the stability of 10.6T token training solely to the optimizer and precision format ignores other potential factors (e.g., data quality, MoE routing stability) that are not ruled out.

Finally, regarding the long-context extension, the authors admit that "Absolute scores are conservative due to a prompt-formatting issue" (Section 3). While they correctly highlight the *relative* improvement of layer-selective YaRN, the phrasing "outperforms uniform RoPE" could be misread as a claim of absolute state-of-the-art performance. The text should be tightened to emphasize that the *ranking* is robust despite the absolute score suppression, preventing readers from over-estimating the model's raw long-context capability.
