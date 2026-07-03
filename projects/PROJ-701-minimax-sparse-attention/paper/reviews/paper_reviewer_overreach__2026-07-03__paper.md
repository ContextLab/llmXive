---
action_items:
- id: edae799fad7c
  severity: writing
  text: The claim of 'on par with GQA' (Abstract, Sec 3) is overreaching given Table
    2 shows a -0.60 point drop on HELMET-128K Overall. The authors must qualify this
    claim to reflect that performance is comparable on general benchmarks but slightly
    degraded on specific long-context retrieval metrics.
- id: fcee3dcdfe08
  severity: writing
  text: The abstract states the model 'performs on par with GQA' while simultaneously
    claiming a 28.4x FLOP reduction. The paper does not provide a direct FLOP-normalized
    comparison to prove that the performance is maintained *at the same compute budget*,
    only at the same parameter count. This conflates efficiency with capability and
    overstates the efficiency gain's impact on quality.
- id: 4170a4619825
  severity: writing
  text: The conclusion claims the method 'preserves capabilities' at 109B scale. However,
    Table 2 shows a 2.40 point gain on HELMET ICL but a 0.60 point loss on Overall,
    and Table 1 shows mixed results (e.g., -1.35 on GSM8K in CPT). The text should
    avoid absolute preservation claims and instead report the specific trade-offs
    observed.
artifact_hash: f00725508246b024cf4aa3c534e6f6afc166e2aa03bee30b44dd04e950f05991
artifact_path: projects/PROJ-701-minimax-sparse-attention/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T09:48:11.451271Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper exhibits a tendency to overstate the universality of its performance preservation claims, particularly in the Abstract and Conclusion. While the authors claim the method "performs on par with GQA" (Abstract) and "preserves capabilities" (Conclusion), the empirical evidence in Table 2 (HELMET-128K) and Table 1 (GSM8K, MMLU) reveals a nuanced picture where performance is not uniformly preserved. Specifically, the HELMET-128K Overall score drops by 0.60 points, and GSM8K drops by 1.35 points in the CPT setting. While these drops are small, the absolute phrasing "on par" and "preserves" suggests a lack of degradation that the data does not fully support. The authors should qualify these claims to acknowledge the specific benchmarks where slight degradation occurs, distinguishing between "general reasoning" (where performance is stable) and "long-context retrieval" (where trade-offs exist).

Furthermore, the claim of a "28.4x" reduction in per-token attention compute (Abstract, Sec 5.3) is technically accurate regarding FLOPs but risks misleading readers regarding the *effective* efficiency gain if the model requires more tokens or steps to converge due to the slight performance dip. The paper does not explicitly state whether the "on par" claim holds under FLOP-normalized conditions (i.e., if the GQA baseline were scaled down to match MSA's compute). Without this normalization, the claim that the method achieves massive speedups *while* maintaining performance is slightly overreaching, as it implies a Pareto improvement that might not exist if the baseline were adjusted for compute. The text should clarify that the comparison is against a full-compute GQA baseline, not a compute-matched one.

Finally, the assertion that the Index Branch value head is "not critical" (Appendix e001) is based on a comparison where the "No-value" variant actually outperforms the "With-value" variant on several key benchmarks (MMLU, MMLU-Pro, BBH). While the authors conclude the head is dropped for efficiency, the data suggests it may be detrimental to performance in some contexts. The conclusion that it is merely "not critical" understates the potential negative impact of the value head on certain tasks, which should be framed more carefully as a performance-efficiency trade-off rather than a neutral removal.
