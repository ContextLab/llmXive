# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 5 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Power analysis assumes a medium effect size (Cohen’s d = 0.5) and targets ≥ 80 % power, but the plan never specifies the number of subjects available in OpenNeuro ds001495. RSA is computed per subject, so statistical power depends critically on subject count, not just story count. Without an explicit subject‑sample size, the power analysis may be overly optimistic.
- Construct validity of the ‘brain‑inspired’ mechanisms is not fully established: the sparse autoencoder’s sparsity ratio and the gating module’s StoryCoherence score are treated as proxies for hippocampal pattern separation and prefrontal executive control, yet no justification is provided that these metrics map onto the neural processes of interest. This weakens the claim that the model is truly brain‑inspired.
- The plan requires **≥ 100** story transcripts (task T025) to proceed, but OpenNeuro ds001495 (the ‘Narratives’ dataset) contains only 27 distinct story stimuli. This violates FR‑001 and FR‑004, making the chosen dataset insufficient for the required statistical power and RSA analysis. A dataset with a larger number of unique stories (e.g., OpenNeuro ds002800 or a different story‑based fMRI collection) should be used.
- FR‑001 mandates downloading and preprocessing OpenNeuro ds001495 to extract BOLD timecourses for left/right hippocampus and DLPFC ROIs. While the dataset provides whole‑brain BOLD data, it does **not** include pre‑computed masks for DLPFC and the number of story events is limited, risking failure of the ROI extraction fallback and insufficient event‑wise averages for RSA.
- The plan references several output artifacts (mixed‑effects summary CSV, power‑analysis CSV, visualizations PNG, and results_summary.csv) that are not defined as entities in data-model.md, leaving no single source of truth for their schema or required fields.
