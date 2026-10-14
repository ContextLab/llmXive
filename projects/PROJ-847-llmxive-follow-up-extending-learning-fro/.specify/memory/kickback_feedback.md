# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 11 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan states an **independent‑samples t‑test** will be used (Phase 4 table) while the research document (research.md) describes a **paired t‑test**. This inconsistency must be resolved and the chosen test justified; using an independent‑samples test discards the within‑seed pairing that could increase power.
- Only **three random seeds** per condition are planned. Power analysis in research.md claims >0.6 power for medium effects, but with n=3 the test is likely under‑powered, risking false negatives. Either increase the number of seeds or provide a more rigorous power calculation that matches the compute budget.
- Logical accuracy is measured by **exact‑match string equality**. While cited as standard, this metric may not capture partial reasoning quality, potentially threatening construct validity. Consider supplementing with a graded metric (e.g., BLEU, ROUGE, or token‑level overlap) or at least acknowledge this limitation.
- The adaptive run’s final accuracy is compared to the fixed ρ = 0.5 baseline, and the result is framed as the adaptive strategy **significantly outperforms** the baseline. The design is comparative, not causal; avoid causal language unless random assignment of density is ensured. Clarify that the claim is about performance difference, not a causal effect of density.
- SC-002 (Functional shape of density‑performance relationship measured via curve fitting) is absent from the plan’s traceability; no explicit link to a phase or contract.
- SC-003 (Statistical significance of adaptive strategy measured by p‑value from paired t‑test) is not mentioned in the plan; the statistical validation phase only cites independent‑samples t‑test but does not tie to SC‑003.
- SC-004 (Stability of identified critical threshold measured by accuracy‑degradation slope) is missing from the plan’s listed success criteria.
- SC-005 (Computational feasibility measured by total wall‑clock time against 6‑hour limit) is not explicitly covered; while FR‑005 mentions a hard timeout, the success criterion SC‑005 is not traced.
- The Verified Datasets table only cites the GSM8K **test split** (parquet) as the dataset source. Training the diffusion model requires the **train split** (or the full dataset). Without a citation and download step for the GSM8K training data, the training pipeline cannot be executed as described, making the plan infeasible. Add a citation and loader for the GSM8K train split (e.g., `datasets.load_dataset("openai/gsm8k", split="train")`).
- Phase 1 output artifact is described as `outputs/fixed_baselines_*.csv` (CSV files), but the contract `training_result.schema.yaml` defines a JSON object schema. The artifact type does not match the contract, creating a plan‑contract mismatch.
- Quickstart commands write a single file `outputs/fixed_baselines.csv`, while the plan states multiple per‑rho/seed CSV files (`outputs/fixed_baselines_*.csv`). This inconsistency may cause confusion about the expected output format and naming.
