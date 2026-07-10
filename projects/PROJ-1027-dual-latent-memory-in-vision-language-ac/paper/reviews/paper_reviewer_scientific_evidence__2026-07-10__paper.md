---
action_items:
- id: 68d28cd50cf7
  severity: writing
  text: The paper presents a compelling architectural shift for VLA models, moving
    memory from external conditioning to native latent tokens. However, the evidentiary
    strength of the reported gains is currently insufficient to rule out noise or
    confounding factors. First, the primary results in Table 1 (SimplerEnv) and Table
    2 (LIBERO) are presented as single-point averages (e.g., 73.9% vs 71.9% for MemoryVLA)
    with no reported standard deviation, confidence intervals, or number of random
    seeds used. In
artifact_hash: 42bc6cf83e8ec23d1633a3d1459efcb214654e063ccd9a00df88a1940764a5ad
artifact_path: projects/PROJ-1027-dual-latent-memory-in-vision-language-ac/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-10T04:25:03.092835Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling architectural shift for VLA models, moving memory from external conditioning to native latent tokens. However, the evidentiary strength of the reported gains is currently insufficient to rule out noise or confounding factors.

First, the primary results in Table 1 (SimplerEnv) and Table 2 (LIBERO) are presented as single-point averages (e.g., 73.9% vs 71.9% for MemoryVLA) with no reported standard deviation, confidence intervals, or number of random seeds used. In robotic manipulation benchmarks, success rates can fluctuate significantly due to random initialization, task sampling, or stochasticity in the environment. A 1.1% or 2.0% margin is often indistinguishable from sampling noise without variance reporting. The authors must report results averaged over at least 3-5 independent training seeds with standard deviations to demonstrate that the improvements are robust and not artifacts of a lucky seed.

Second, the ablation study in Table 3 attributes performance gains to the "dual-scale" nature of the memory. While removing both streams causes a large drop, the individual removals of short-term or long-term memory show moderate drops (~8-9%). The paper does not rule out the alternative explanation that the gain comes simply from increasing the total number of memory tokens (context length) rather than the specific dual-scale mechanism. To isolate the contribution of the dual-scale design, the authors should add a control experiment where a single memory stream is expanded to match the total token count of the dual-stream model (e.g., 12 tokens in one stream vs 8+4). If the single-stream model performs similarly, the "dual-scale" claim is weakened.

Finally, the comparison between "Latent-native" and "Policy-side" memory (Table 4) requires clarification on the retrieval and condensation pipeline. The text implies the baseline uses "external policy-side condition," but it is unclear if this baseline uses the same number of retrieved units ($K=8$) and the same condenser architecture, or if it uses raw retrieved evidence. If the baseline uses raw tokens or a different retrieval budget, the comparison confounds the "latent-native" integration with the benefits of better compression or retrieval. The authors must explicitly state that the baseline uses identical retrieval and condensation logic, differing only in the injection point (input sequence vs. external conditioning), to validly isolate the architectural contribution.
