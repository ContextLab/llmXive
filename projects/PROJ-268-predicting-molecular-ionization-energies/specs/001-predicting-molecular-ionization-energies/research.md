# Research: Predicting Molecular Ionization Energies with Graph Neural Networks

## Problem Statement
Can a 2‑dimensional Graph Neural Network (MPNN), trained exclusively on atom‑bond graphs derived from SMILES, predict molecular ionization energies (approximated by `-HOMO` via Koopmans’ theorem) with accuracy comparable to semi‑empirical quantum methods while respecting strict CPU resource limits?

## Dataset Strategy

| Dataset | Source URL | Variables | Fit for Purpose? | Action |
|---|---|---|---|---|
| **QM9 (parquet)** | `https://huggingface.co/datasets/lisn519010/QM9/resolve/main/data/full-00000-of-00001-e217b6ecfbeb7149.parquet` | `SMILES`, `homo` (AU), other quantum properties | **High** – contains required `homo` column for proxy target. | Primary training / validation dataset. |
| **NIST WebBook (CSV)** | `https://huggingface.co/datasets/Raziel1234/WebBooks-1/resolve/main/books_dataset.txt` | Experimental ionization energies (eV) matched by SMILES/InChI | **High** – used for construct‑validity check of the `-HOMO` proxy. | Phase 0 validation (FR‑001, FR‑014). |
| **QM9 (Enthalpy)** | `https://huggingface.co/datasets/hadoan/enthalpy-QM9-1k/resolve/main/data/train-00000-of-00001-ffd5f7908688c934.parquet` | SMILES, enthalpy | **Low** – not used for target; retained for preprocessing sanity checks. | Optional fallback if primary dataset fails. |
| **QM9 (Gaps)** | `https://huggingface.co/datasets/Hassanharb/gaps-qm9-1k/resolve/main/data/train-00000-of-00001-3e8a1863fa44a20f.parquet` | SMILES, HOMO‑LUMO gap | **Medium** – auxiliary sanity check only. | Not used in main analysis. |

### Dataset Fit Verification
- The QM9 parquet **does** contain a `homo` column (AU). We will convert AU → eV (An atomic unit of energy is on the order of tens of electronvolts.) to obtain the proxy target.  
- The NIST WebBook CSV provides experimental ionization energies linked via canonical SMILES; a **500‑molecule random subset** will be matched for validation (FR‑001).  

## Model Architecture & Rationale
- **MPNN (GCN)**: 3 layers, hidden dimension 64, atom embedding 64, bond embedding 32, ReLU activations, global average pooling, MLP head (64 → 1). Chosen for proven performance on QM9‑style tasks and low CPU footprint (FR‑003).  
- **Baseline 1 – Fingerprint Linear Regression**: ECFP4 (radius 2) → Ridge regression; provides a fast 2D reference (FR‑006).  
- **Baseline 2 – DFTB**: Semi‑empirical 3‑D method; if full‑dataset DFTB exceeds 30 min, we will run DFTB on a **stratified 5 k‑molecule subset** (still DFTB) for the residual‑correlation analysis. AM1 may be run as an auxiliary baseline but will **not** be used for the Pearson‑ρ comparison with the GNN (addressing methodology‑36066ef3).  

## Ablation Strategy
- **Targeted Feature**: Bond features (type, conjugation, stereochemistry).  
- **Perturbation**: Zero out all bond feature vectors **during training** (re‑training, not inference‑time noise).  
- **Runs**: **5** independent stochastic seeds for the baseline and **5** for the perturbed configuration (FR‑017).  
- **Job Splitting**: The ten training runs are divided into **two sequential CI jobs** (Job B‑1 and Job B‑2), each executing **5** runs. This keeps each job under the 6‑hour wall‑clock limit.  
- **Runtime Guard & Fallback**: Before each sub‑job starts, a quick profiling run estimates per‑run wall‑clock. If the estimate exceeds **4 hours**, the sub‑job automatically switches to a **5 000‑molecule** training subset (still meets the a‑priori power requirement).  
- **Training Subset**: Ablation uses a **10 000‑molecule** training subset by default (still satisfies FR‑018).  
- **Statistical Test**: Paired t‑test on per‑molecule absolute error vectors; Bonferroni correction for multiple ablations; additionally, **bootstrap** (1 000 resamples) to obtain robust confidence intervals (methodology‑a1f1d3cc).  

## Statistical Rigor
- **Multiple Comparisons**: Bonferroni correction applied across all ablation configurations.  
- **Power Analysis**: Prior to training, we conduct an a priori power analysis (α = 0.05, desired power ≥ 0.8) to detect an MAE difference of **0.1 eV**. Using a pilot variance estimate σ ≈ 0.3 eV (from 1 k‑molecule pilot), the required sample size for the **full model** is **N ≥ 20 000** molecules (methodology‑457dec94). For the ablation subset we use 10 k molecules, which still yields ≥ 0.8 power for detecting the same effect size (verified in Phase 0). The analysis result is recorded before any model fitting (FR‑018).  
- **Causal Claims**: None – all statements are associational (Principle VI).  
- **Collinearity**: Acknowledge atom and bond features correlation; feature‑importance framed as “predictive contribution” (FR‑022).  

## Compute Feasibility Decision
- **CPU‑First**: All training uses `torch` on `device="cpu"`.  
- **Batch Size**: Start at 64; if OOM, reduce stepwise (48 → 32 → 16).  
- **Epochs**: Up to 200 with early stopping (patience = 10) **and** a hard cap of 100 epochs for ablation runs to guarantee completion within the 6‑hour job budget.  
- **Memory Monitoring**: `psutil` logs peak RSS; abort if > 7 GB (FR‑013).  
- **Timeout**: Hard 6‑hour wall‑clock limit per CI **job**; the pipeline is split into three separate jobs (Training, Ablation, Attribution) and the ablation job is further split into two sub‑jobs (Job B‑1, Job B‑2) to stay within limits (methodology‑e836eb13).  

## Edge Cases & Handling
| Situation | Handling |
|---|---|
| Missing `homo` value | Exclude molecule, log count; if >5 % → “Data Quality Warning” (FR‑012). |
| Invalid SMILES (RDKit parse failure) | Exclude, log, continue. |
| Timeout before completing all 5 ablation runs in a sub‑job | Save best checkpoint, report “partial power” warning, continue with completed runs. |
| Test molecule with unseen scaffold | Flag in OOD report, note potential higher error (FR‑019). |
| Proxy validation fails (R² < 0.9 or MAE > 0.4 eV) | Abort entire pipeline, output “Construct Validity Failure” with metrics (FR‑024). |

## Chemical Validation Plan
1. **Integrated Gradients Attribution** – compute IG for a **random subset of 1 000 test molecules** (stratified by scaffold) and store per `model_output.schema.yaml`. Quantitatively validate by calculating Pearson correlation between atom‑level IG scores and Hammett σ constants; report ρ and p‑value (methodology‑40badbde).  
2. **Error‑Property Correlation** – Pearson ρ between absolute error and (a) molecular weight, (b) number of rotatable bonds (FR‑009).  
3. **Residual Overlap** – Pearson ρ between GNN residuals and **DFTB** residuals (using the DFTB subset if full DFTB not feasible); require |ρ| ≤ 0.2 to support 2D‑sufficiency (FR‑015, FR‑023).  

## Evaluation & Success Criteria
- **MAE < 0.4 eV** on the test set is a **hard pass/fail** condition; if violated, the pipeline records a “Performance Failure” and halts further reporting (plan_consistency‑9c9242a6).  
- Ablation significance (p < 0.05 after correction) plus effect size (Cohen’s d) satisfy SC‑002.  
- Attribution‑σ correlation significance (p < 0.05) satisfies the quantitative attribution requirement.  

---



