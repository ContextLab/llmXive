# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 5 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan states a *Minimum‑N power check* ("Tests run only if analyzable PR count ≥ 100") but provides no quantitative power analysis (e.g., expected effect size, α, β) to justify that 100 PRs is sufficient for McNemar’s test and chi‑square. Without a formal power calculation the statistical claims may be under‑powered.
- Potential confounds such as repository‑level differences, PR size, and presence of LLM‑generated code are not explicitly modelled or controlled. The plan flags LLM‑generated code (FR‑016) but does not describe how these PRs will be excluded or adjusted for in the comparative analysis, risking biased estimates of LLM‑assisted review quality.
- Alignment relies on a fixed similarity threshold (≥ 0.85) and Jaccard overlap (≥ 0.5). The choice of these thresholds is not justified nor linked to any validation study, which may affect construct validity of the matched bug set.
- FR-014 ('System MUST explicitly state in the final report that the term "affect" ... is interpreted as "correlate with"') is absent from the plan. No reporting task mentions this required clarification.
- The plan states that `src.inference.run_inference` loads `bigcode/starcoder2-3b` in `torch.float16` with `low_cpu_mem_usage=True`. Float16 tensors are not supported on CPU‑only PyTorch builds and will raise a runtime error, making the inference step infeasible on the GitHub Actions free‑tier runner (CPU‑only, ≤7 GB RAM). The model should be loaded in a CPU‑compatible dtype (e.g., `torch.float32` or 8‑bit quantized) or a smaller model should be used to stay within the memory/compute budget.
