# Research: Predicting Molecular Packing Efficiency from SMILES Representations

## Objective
Determine whether 2‑D molecular topology encoded as SMILES, when transformed into learned fingerprint vectors, can predict crystal packing efficiency (packing coefficient) for organic crystals from the Crystallography Open Database (COD).

## Dataset Strategy

| Dataset | Source | Access Method | Notes / Verification |
|---------|--------|---------------|----------------------|
| COD (Crystallographic Open Database) | Official COD archive (download script) | `curl`/`wget` of the COD tarball (URL obtained from COD website) | **No verified URL** in the “Verified datasets” block; we will use the official COD download procedure as described in COD documentation. |
| van der Waals radii (Bondi table) | Bondi (1964) | Hard‑coded table in `utils/chemistry.py` | Not a separate dataset; internal constant. |
| Pre‑trained SMILES‑Transformer | HuggingFace hub (`seyonec/PubChem10M_SMILES_BPE_60k`) | `transformers.AutoModel.from_pretrained(..., trust_remote_code=True)` | Model is CPU‑compatible; no external citation required in the pipeline. |

*If any of the above sources become unavailable, the pipeline will abort with a clear error message and the failure will be logged.*

## Pipeline Overview

1. **Data Acquisition (FR‑001)**
   - Run `pipelines/download_cod.py` to fetch the latest COD release.
   - Verify checksum of the downloaded archive; record in `state/projects/...yaml`.

2. **Filtering (FR‑001)**
   - Parse each CIF; retain entries where the number of non‑hydrogen atoms < 50 **and** the chemical composition is organic (C, H, N, O, S, P, halogens only).
   - Log the number of retained entries.

3. **Parsing & Packing Coefficient (FR‑002)**
   - Extract unit‑cell parameters (`a, b, c, α, β, γ`) → compute unit‑cell volume.
   - For each atom, lookup Bondi vdW radius, compute atomic vdW volume (`4/3·π·r³`), sum to obtain `vdw_volume_sum`.
   - Packing coefficient = `unit_cell_volume / vdw_volume_sum`.
   - Entries lacking required CIF fields are skipped with a warning (edge case handling).

4. **SMILES Generation (FR‑003)**
   - Convert atomic coordinates to a molecular graph using RDKit’s `MolFromMolBlock`.
   - Generate canonical SMILES (`Chem.MolToSmiles(..., canonical=True)`).
   - Failures (e.g., ambiguous stereochemistry) are logged and the entry excluded.

5. **Fingerprint Extraction (FR‑004)**
   - Load the frozen SMILES‑Transformer (`AutoModel` + `AutoTokenizer`).
   - Tokenize each SMILES, pass through the transformer, mean‑pool hidden states → fixed‑length fingerprint (e.g., 768‑dim).

6. **Dataset Assembly (FR‑010)**
   - Assemble a CSV `data/processed/dataset.csv` with columns: `cod_id`, `smiles`, `unit_cell_volume`, `vdw_volume_sum`, `packing_coefficient`, `fingerprint` (JSON‑encoded list), plus provenance metadata.
   - Split into training ([deferred]) and validation ([deferred]) using `train_test_split(..., random_state=42)`.
   - **Contract Validation**: Run `pytest -q` to validate `dataset.csv` against `contracts/dataset.schema.yaml`.

7. **Model Training (FR‑005)**
   - Define a 2‑layer fully‑connected MLP (`MLP-128-1`):
     - Input dim = fingerprint size (must be 768).
     - Hidden layer = 128 units, ReLU.
     - Output layer = 1 unit (linear).
   - Total parameters ≈ 98 k (≤ 100 k).  
   - Train for ≤ 5 epochs with Adam optimizer, learning rate 1e‑3, batch size 32.
   - Early stopping on validation loss; if convergence not reached, log a warning and keep best‑so‑far model.
   - Save model checkpoint `models/model.pt`.
   - **Contract Validation**: Run `pytest -q` to validate `model.pt` against `contracts/model.schema.yaml`.

8. **Model Evaluation (FR‑006, FR‑011)**
   - Predict on validation set.
   - Compute **MAE**, **Pearson r**, **Spearman ρ**.
   - Generate scatter plot (`pred vs true`) and residual diagnostics:
     - Shapiro‑Wilk test on residuals (α = 0.05, require p > 0.05).
     - Breusch‑Pagan test for heteroscedasticity (require p > 0.05).
   - Record all metrics, diagnostic p‑values, and **Spearman ρ ≥ 0.4** in `report.txt` (SC‑006).

9. **Statistical Significance & Robustness (FR‑007, FR‑008)**
   - **Permutation test**: Shuffle the target vector many times, recompute Pearson r each time, obtain empirical p‑value. **Success criterion**: p < 0.05 (SC‑003).
   - **Sensitivity sweep**: Repeat permutation test using α = 0.01 and α = 0.10; verify that the significance decision (p < α) is unchanged (SC‑004).

10. **Logging & Reporting (FR‑009)**
    - All steps write structured logs (`pipeline.log`) and a human‑readable `report.txt`.
    - Final artifacts: `data/processed/dataset.csv`, `models/model.pt`, `figures/*.png`, `report.txt`.

## Decision / Rationale
- **CPU‑only SMILES‑Transformer**: The selected model (< 100 MB) runs comfortably on the CI runner without GPU.
- **MLP size**: Hidden layer of 128 units yields ≤ 100 k parameters, satisfying FR‑005 while remaining expressive.
- **Epoch limit**: ≤ 5 epochs keep runtime well under the 6‑hour budget; early stopping mitigates under‑fitting.
- **Permutation test**: 1 000 permutations provide a stable p‑value estimate while remaining cheap (< 2 min).
- **Power analysis**: Targeting **≥ 950** curated entries gives two‑tailed power ≈ 0.90 for an expected r ≈ 0.4. If COD provides fewer entries, the pipeline will use all available organic entries up to 1 000 and explicitly note the reduced power in `report.txt`.
- **Methodological limitations**: SMILES captures only 2‑D connectivity; packing coefficient is a proxy that ignores crystal‑specific factors (e.g., voids, solvent). Results are interpreted as exploratory associations, not causal statements.

## Statistical Rigor Checklist
- **Multiple‑comparison correction**: Not required (single primary correlation test).  
- **Power justification**: N ≥ 950 → power ≈ 0.90 for r ≈ 0.4 (≥ 0.80 target). If N < 950, reduced power is reported.  
- **Causal inference**: Observational; claims limited to association.  
- **Measurement validity**: Packing coefficient derived from standard crystallographic calculations; vdW radii from Bondi (1964). SMILES‑Transformer pretrained on 10 M SMILES (publicly documented).  
- **Collinearity**: Fingerprint dimensions are highly correlated by design; the MLP treats the vector as a whole, and no independent‑predictor claims are made.

## Success Criteria (explicit mapping to SCs)
- **SC‑001**: Pearson r ≥ 0.4 (predictive) **or** r < 0.2 (null finding) on the validation set.  
- **SC‑002**: MAE ≤ 0.05 on the validation set.  
- **SC‑003**: Permutation‑test p‑value < 0.05.  
- **SC‑004**: Significance decision unchanged for α = 0.01, 0.05, 0.10.  
- **SC‑005**: End‑to‑end pipeline completes on free‑tier CI within 6 h, ≤ 2 GB RAM.  
- **SC‑006**: Diagnostic thresholds – Shapiro‑Wilk p > 0.05, no heteroscedasticity (Breusch‑Pagan p > 0.05), Spearman ρ ≥ 0.4; all recorded in `report.txt`.

---


## Edge Cases

- **Missing CIF parameters**: Logged, entry skipped, pipeline continues.  
- **SMILES generation failures**: Entry flagged, excluded, warning emitted.  
- **MLP non‑convergence**: Early stop, warning logged, best‑so‑far model saved for downstream evaluation.

## Projects/PROJ-511-predicting-molecular-packing-efficiency‑/specs/001-predicting-molecular-packing-efficiency/contracts (validation)

- All contracts (`dataset.schema.yaml`, `model.schema.yaml`) are validated via `pytest -q` after dataset creation and model checkpointing.
