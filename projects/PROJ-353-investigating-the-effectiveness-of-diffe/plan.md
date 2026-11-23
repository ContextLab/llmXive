# Implementation Plan: Investigating Loss Functions on Small-World Graphs

## Summary
This project investigates the effectiveness of contrastive (InfoNCE) vs. classification (Cross-Entropy) loss functions for training Graph Neural Networks (GNNs) on small-world graphs. We generate Watts-Strogatz graphs with varying rewiring probabilities ($\beta$), train 2-layer GCNs, and analyze convergence speed.

**Sample Size**: N=110 (justified by formal power analysis in `data/power_analysis_output.json`).
**Convergence Threshold**: $\ge 0.90$ accuracy.
**Max Epochs**: 1000 (censoring limit).

## Compute Feasibility
All training runs on CPU. With N=110 graphs and max 1000 epochs per run, total compute is estimated to be well within the 6-hour CI limit (approx. 2-3 hours expected). [UNRESOLVED-CLAIM: c_1545d9f5 — status=not_enough_info]

## Methodology
1. **Data Generation**: Generate 110 Watts-Strogatz graphs (10 per $\beta \in [0.0, 1.0]$ step 0.1). [UNRESOLVED-CLAIM: c_dd9fe7e9 — status=not_enough_info] Annotate nodes with community labels derived from the initial lattice.
2. **Training**: Train two models per graph:
 - **Cross-Entropy**: Standard supervised node classification.
 - **InfoNCE**: Contrastive pre-training followed by a frozen linear probe.
3. **Analysis**:
 - **Tobit Regression**: Models `steps_to_convergence` as a function of `loss_type`, `beta`, and their interaction, handling censored data (runs that didn't converge by 1000 epochs).
 - **Cox Proportional Hazards**: Survival analysis to compare hazard rates of convergence between loss types.
4. **Interaction Focus**: Analysis is scoped strictly to interaction terms between $\beta$ and loss type.

## Success Criteria
The study is considered successful if it can determine whether contrastive loss converges faster as graph randomness ($\beta$) increases.

**Statistical Significance Definition**:
- We perform two interaction tests: one for Tobit Regression and one for Cox Proportional Hazards.
- We apply **Bonferroni correction** to the p-values of these two interaction terms.
- The `is_significant` flag in `data/analysis_results.json` is set to `True` if and only if the **minimum Bonferroni-corrected p-value** across both models is **< 0.05**.
- Formula: $p_{corrected} = p_{raw} \times 2$. Condition: $\min(p_{corrected\_tobit}, p_{corrected\_cox}) < 0.05$.

## Spec Alignment Note
- **FR-006/FR-007**: Updated to use Tobit Regression and Cox Proportional Hazards instead of ANCOVA/Pearson correlation.
- **FR-005**: Convergence threshold defined as $\ge 0.90$.
- **US-2**: Censoring logic implemented at 1000 epochs.

## Project Structure
- `code/`: Source code (power_analysis.py, utils.py, models.py, losses.py, train.py, data_generation.py, analyze.py, main.py)
- `data/`: Raw data, logs, and analysis results
- `contracts/`: JSON schemas for data exchange
- `tests/`: Unit tests