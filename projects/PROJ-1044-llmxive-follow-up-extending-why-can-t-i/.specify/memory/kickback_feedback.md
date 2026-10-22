# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 5 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'science'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The selection criteria (optical‑flow divergence ≤ 0.15 **and** ResNet‑18 cosine similarity ≥ 0.9) introduce a potential confound: they preferentially retain counterfactuals that are visually similar to the original, which may make the task easier and artificially inflate the observed reduction in ΔAcc. This selection bias is not addressed, risking that the reported robustness gains stem from easier examples rather than genuine increased motion reliance.
- The power analysis assumes an effect size d ≈ 0.8 without empirical justification. If the true effect is smaller, the 10‑seed design may be under‑powered, leading to false‑negative conclusions. The plan should either provide a data‑driven estimate of the expected effect size or increase the number of seeds/replicates to ensure adequate power.
- ΔAcc is used as the primary indicator of ‘reliance on motion cues’, but a lower ΔAcc could also arise from the model learning to ignore object information altogether rather than truly leveraging motion. The plan does not include an explicit analysis (e.g., probing the learned feature space or an ablation that removes motion features) to disambiguate these possibilities, limiting construct validity.
- The plan references using frozen **FlowNet‑C** features for video representation (Phase 1) but does not provide a citation or URL to the original FlowNet‑C source/model repository. All external models or datasets used must be cited per the data‑resource guidelines.
- The primary validation metric ΔAcc (accuracy drop between original and counterfactual videos) is directly optimized by the Counterfactual Consistency (CC) loss, which penalizes prediction changes on counterfactual pairs. Evaluating that the CC‑loss reduces ΔAcc is therefore circular: the model is trained to minimise exactly this quantity, so the reported improvement is guaranteed by definition rather than providing independent evidence that the model relies more on motion cues.
