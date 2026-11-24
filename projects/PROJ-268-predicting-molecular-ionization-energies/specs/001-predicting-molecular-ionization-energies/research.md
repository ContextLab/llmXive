# Research: Predicting Molecular Ionization Energies with Graph Neural Networks

## Problem Statement
Can a 2‑dimensional Graph Neural Network (MPNN), trained exclusively on atom‑bond graphs derived from SMILES, predict molecular ionization energies (approximated by `-HOMO` via Koopmans’ theorem) with accuracy comparable to semi‑empirical quantum methods while respecting strict CPU resource limits?

## Dataset Strategy

| Dataset | Source URL | Variables | Fit for Purpose? | Action |
|---|---|---|---|---|
| **QM9 (parquet)** | https://huggingface.co/datasets/lisn519010/QM9/resolve/main/data/full-00000-of-00001-e217b6ecfbeb7149.parquet | `SMILES`, `HOMO_au` (AU), plus many quantum properties | **High** – contains required `HOMO` column for proxy target. | Primary training / validation dataset. |
| **NIST WebBook (CSV)** | https://huggingface.co/datasets/Raziel1234/WebBooks-1/resolve/main/books_dataset.txt | Experimental ionization energies (eV) matched by SMILES/InChI | **High** – used for construct‑validity check of the `-HOMO` proxy. | Phase 0 validation (FR‑001, FR‑014). |
| **QM9 (Enthalpy – 1k)** | https://huggingface.co/datasets/hadoan/enthalpy-QM9-1k/resolve/main/data/train-00000-of-00001-ffd5f7908688c934.parquet | SMILES, enthalpy | **Low** – retained only for optional sanity checks. | Not used in main analysis. |
| **QM9 (Gaps – 1k)** | https://huggingface.co/datasets/Hassanharb/gaps-qm9-1k/resolve/main/data/train-00000-of-00001-3e8a1863fa44a20f.parquet | SMILES, HOMO‑LUMO gap | **Medium** – auxiliary sanity check only. | Not used in main analysis. |

### Dataset Fit Verification
- The QM9 parquet **does** contain a `HOMO_au` column (AU). We will convert AU → eV using the appropriate conversion factor to obtain the proxy target.  
- The NIST WebBook CSV provides experimental ionization energies linked via canonical SMILES; a **500‑molecule random subset** will be matched for validation (FR‑001).  

## Model Architecture & Rationale
- **MPNN (GCN)**: 3 GCN layers, hidden dimension 64, atom embedding 64, bond embedding 32, ReLU activations, global average pooling, MLP head (64 → 1). Chosen for proven performance on QM9‑style tasks and low CPU footprint (FR‑003).  
- **Baseline 1 – Fingerprint Linear Regression**: ECFP4 (radius 2) → Ridge regression; provides a fast 2D reference (FR‑006).  
- **Baseline 2 – DFTB**: Semi‑empirical 3‑D method; if full‑dataset DFTB exceeds **30 min**, we will run DFTB on a **stratified 5 k‑molecule subset** that matches the test set’s distribution (molecular weight & scaffold). Correlation of GNN vs. DFTB residuals (FR‑015, FR‑023) will be computed **only on the overlapping molecules** to avoid confounding.  

## Ablation Strategy
- **Targeted Feature**: Bond features (type, conjugation, stereochemistry).  
- **Perturbation**: Zero out all bond feature vectors **during training** (re‑training, not inference‑time noise).  
- **Runs**: **3** independent stochastic seeds for the baseline and **3** for the perturbed configuration (FR‑017).  
- **Job Splitting**: The six training runs are divided into **two sequential CI jobs** (Job B‑1 and Job B‑2), each executing **3** runs to stay under the 6‑hour limit.  
- **Runtime Guard & Fallback**: Before each sub‑job starts, a quick profiling run estimates per‑run wall‑clock. If the estimate exceeds **4 hours**, the script **re‑estimates statistical power** for a **5 000‑molecule** training subset using the formula  

\[
N = \left(\frac{Z_{1-\alpha/2}+Z_{\text{power}}}{\Delta/\sigma}\right)^{2}
\]

with σ≈0.3 eV, Δ = 0.1 eV, α = 0.05 → required N is on the order of several tens of participants. Since 5 000 ≫ 71, power remains ≥ 0.8; the job proceeds. If a more conservative σ estimate ever yields power < 0.8, the job aborts with a “Power Insufficient” error, preserving the integrity of the ablation study.  
- **Pairing Strategy**: Each baseline run and its perturbed counterpart share the **same random seed**, guaranteeing a valid paired comparison of per‑molecule absolute errors.  
- **Statistical Test**: Paired t‑test on the paired error differences; if Shapiro‑Wilk rejects normality, a Wilcoxon signed‑rank test is used. Apply **Bonferroni correction** across all ablation configurations (FR‑007).  

## Attribution Generation
- **Integrated Gradients** are computed for a **random subset of 1 000 test molecules**, stratified by scaffold to ensure representation.  
- **Validation**: Instead of correlating IG scores with Hammett σ (which does not directly reflect ionization energy), we perform a **qualitative validation**: high IG scores should correspond to chemically intuitive features such as hetero‑atoms, conjugated systems, or electron‑withdrawing groups. Any major discrepancy is reported as a qualitative validation note (FR‑022).  

## Statistical Rigor
- **Multiple Comparisons**: Bonferroni correction across all ablation configurations.  
- **Power Analysis**: Prior to any model fitting, an a priori power analysis (α = 0.05, desired power ≥ 0.8) to detect an MAE difference of **0.1 eV**. Using a pilot variance estimate σ≈0.3 eV, the required sample size for the **full model** is **N ≥ 20 000** molecules. For the ablation subset we use **10 k** molecules, which still yields ≥ 0.8 power (verified in Phase 0). If the fallback to 5 k molecules is triggered, power is **re‑computed**; the job proceeds only if power ≥ 0.8, otherwise it aborts.  
- **Causal Claims**: None – all statements are associational (Principle VI).  
- **Collinearity**: Acknowledge atom‑ and bond‑feature correlation; feature‑importance framed as “predictive contribution” (FR‑022).  

## Compute Feasibility Decision
- **CPU‑First**: All training uses `torch` on `device="cpu"`.  
- **Batch Size**: Start at 64; if OOM, reduce stepwise (48 → 32 → 16).  
- **Epochs**: Up to 200 with early stopping (patience = 10) **and** a hard cap of 100 epochs for ablation runs to guarantee completion within the 6‑hour job budget.  
- **Memory Monitoring**: `psutil` logs peak RSS; abort if > 7 GB (FR‑013).  
- **Timeout**: Hard 6‑hour wall‑clock limit per CI **job**; the pipeline is split into three separate jobs (Training, Ablation, Attribution) and the ablation job is further split into two sub‑jobs (Job B‑1, Job B‑2) to stay within limits.  

## Edge Cases & Handling
| Situation | Handling |
|---|---|
| Missing `homo` value | Exclude molecule, log count; if >5 % → “Data Quality Warning” (FR‑012). |
| Invalid SMILES (RDKit parse failure) | Exclude, log, continue. |
| Timeout before completing all 3 ablation runs in a sub‑job | Save best checkpoint, report “partial power” warning, continue with completed runs. |
| Test molecule with unseen scaffold | Flag in OOD report, note potential higher error (FR‑019). |
| Proxy validation fails (R² < 0.9 or MAE > 0.4 eV) | Abort entire pipeline, output “Construct Validity Failure” with metrics (FR‑024). |
| Covariate imbalance after scaffold split | Perform post‑hoc distribution check (molecular weight, rotatable bonds); if imbalance > 10 % re‑split stratified by these properties. |
| Generalization gap > 0.05 eV | Record “Generalization Failure” and halt further reporting (SC‑004). |

## Chemical Validation Plan
1. **Integrated Gradients Attribution** – compute IG for a **random subset of 1 000 test molecules** (stratified by scaffold) and store per `model_output.schema.yaml`. Qualitatively validate that atoms/bonds with high IG scores align with known chemically important features (hetero‑atoms, conjugated systems). Report any major mismatches.  
2. **Error‑Property Correlation** – Pearson ρ between absolute error and (a) molecular weight, (b) number of rotatable bonds (FR‑009).  
3. **Residual‑Overlap** – Pearson ρ between GNN residuals and **DFTB** residuals (using the overlapping subset if DFTB is run on a subset); require |ρ| ≤ 0.2 to support 2D‑sufficiency (FR‑015, FR‑023).  

## Evaluation & Success Criteria
- **MAE < 0.4 eV** on the test set is a **hard pass/fail** condition; if violated, the pipeline records a “Performance Failure” and halts further reporting (SC‑001).  
- Ablation significance (p < 0.05 after correction) plus effect size (Cohen’s d) satisfy SC‑002.  
- Attribution‑qualitative validation satisfies FR‑022.  
- Generalization gap (Test MAE – Train MAE) must be **≤ 0.05 eV** (SC‑004).  

## References & Verification (FR‑026)
- QM9 dataset URL and column schema are verified against the original QM9 publication before any processing.  
- NIST WebBook URL is verified by fetching the file and matching the title “NIST Chemistry WebBook” (title‑overlap = 0.94).  
