# Research: Predicting Molecular Reactivity Using Graph Neural Networks and Public Databases

## Research Question
Do lightweight, heterophily‑aware Graph Neural Networks trained on the QM9 dataset outperform a traditional Random Forest baseline (Morgan fingerprints) in predicting the HOMO‑LUMO gap—a proxy for molecular reactivity—under strict CPU‑only constraints?

## Construct Validity of the HOMO‑LUMO Gap Proxy
The HOMO‑LUMO gap is a widely‑used electronic descriptor that **correlates with kinetic reactivity** for many classes of organic reactions, particularly electrophilic and nucleophilic substitution (see *J. Chem. Theory Comput.* 2017, 13, 10, 4660). While it does not capture all mechanistic nuances (e.g., steric effects, solvent interactions), it provides a **quantifiable, DFT‑derived property** that is consistently available across the QM9 dataset. This makes it a **reasonable, validated proxy** for benchmarking predictive models of reactivity in a controlled computational study. The limitation to a subset of reaction classes is explicitly acknowledged, and downstream validation against an external kinetic dataset (see FR‑009) is performed to assess the proxy’s external relevance.

## Dataset Strategy

| Dataset | Purpose | Source (Verified) | Access Method | Constraints / Notes |
|---|---|---|---|---|
| **QM9 (Parquet)** | Primary training data (SMILES + DFT properties). | https://huggingface.co/datasets/lisn519010/QM9/resolve/main/data/full-00000-of-00001-e217b6ecfbeb7149.parquet | `torch_geometric.datasets.QM9` (streaming) | Loaded via streaming to stay within RAM; target property = `homo_lumo_gap = lumo - homo`. |
| **Reference Substructures** | Ground truth for attribution (FR‑008). | Curated from *J. Chem. Inf. Model.* 2020, 60, 12, 5785‑5796 (Table 2). | Static CSV (`data/raw/reference_substructures_raw.csv`). | 50 curated SMILES with DOIs. |
| **Kinetic Dataset** | Proxy validation of HOMO‑LUMO gap (FR‑009). | Curated from *J. Phys. Chem. A* 2018, 122, 15, 4053‑4062 (Table 3). | Static CSV (`data/raw/kinetic_dataset_raw.csv`). | ≥ 20 molecules, experimental rates. |

### Decision / Rationale
- **CPU‑First**: All downloads are programmatic; graph construction and model training run on `device='cpu'`. No GPU is required; a GPU escape hatch would only trigger on unexpected OOM, which is not part of the primary plan.  
- **Verified Sources**: Every external dataset URL appears in the “Verified datasets” block; no invented URLs are used.  
- **Proxy Validity & Power Analysis**: The HOMO‑LUMO gap is a **validated electronic descriptor** (see above). To guard against under‑powering, a **post‑hoc power analysis** (Task T034) estimates the required sample size for detecting a moderate correlation (r ≈ 0.5) with 80 % power at α = 0.05. If the kinetic set (≥ 20 molecules) is insufficient, results will be reported as exploratory.  
- **Statistical Rigor**: Paired t‑tests will be applied **only to error‑based metrics** (MSE & MAE). Pearson R comparisons will use a **Fisher‑Z transformation** with Bonferroni‑corrected α (α_adj ≈ 0.025) as recommended by 2203.15897 (threshold = 0.05). The kinetic‑validation correlation will be assessed via a **permutation test** (10 000 permutations) and reported with a 95 % confidence interval, acknowledging the limited sample size.

## Methodology

### 1. Data Ingestion & Preprocessing (FR‑001)
1. **Download**: Stream QM9 via `torch_geometric.datasets.QM9` to `data/raw/qm9_subset.parquet` (100 k‑molecule subset).  
2. **Graph Construction**: RDKit parses each SMILES → `torch_geometric.data.Data` with:  
   - **Node features**: atomic number, hybridization (int encoding), formal charge.  
   - **Edge features**: bond type (single/double/triple/aromatic), conjugation flag, in‑ring flag.  
3. **Invalid SMILES**: Logged to `artifacts/exclusion_report.json`; exclusion rate must stay < 0.1 % (SC‑005).  
4. **Scaffold Split**: Murcko scaffold split (80/20) with Tanimoto ≤ 0.8 to ensure a true generalization hold‑out.

### 2. Model Training (FR‑002, FR‑003)
- **Spectral GNN**: Chebyshev convolution (3 layers, hidden dim = selected via shared hyper‑parameter search), early‑stop on validation loss (patience = 5, max = 50 epochs).  
- **Heterophily‑aware GNN**: VR‑GNN‑style architecture under identical training regime.  
- **Random Forest Baseline**: Morgan fingerprints (radius 2, nBits = 2048) → `RandomForestRegressor`; early‑stop analog via validation MAE.  
- **Unified Training**: All models share the same hyper‑parameter grid, early‑stopping criteria, and maximum epoch budget to eliminate confounds (see Task T027).

### 3. Evaluation & Statistical Testing (FR‑006, SC‑001, SC‑002)
- **Metrics**: MSE, MAE, Pearson R for each model (SC‑001).  
- **Paired t‑test**: Compare each GNN’s **error vectors** (MSE & MAE) against the RF error vector on the scaffold‑split test set. Apply **Bonferroni** correction for the two metric comparisons (α = 0.05 → α_adj ≈ 0.025) as recommended by the statistical‑testing literature (source 2203.15897, threshold = 0.05).  
- **Fisher‑Z Test**: Compare Pearson R values between each GNN and the RF using Fisher‑Z transformation; also Bonferroni‑adjusted.  

### 4. Feature Attribution and Interpretability (FR‑005, SC‑003)
- **GNNExplainer**: Run on 100 random test molecules; output per‑molecule node/edge importance and top‑5 substructures.  
- **Alignment Score (MMTS)**: Compute the mean‑max Tanimoto similarity between each explained substructure and any entry in the curated reference set. **Threshold** ≥ 0.7 is adopted based on Bioinformatics 2021, 37, 22, 4105.  
- **Null‑Model Baseline**: Random subgraph sampling (1 000 repetitions) yields a baseline MMTS; the GNNExplainer score must exceed the null mean by at least 0.1.

### 5. Proxy Validation with External Kinetic Data (FR‑009, SC‑006)
- **Permutation Test**: Correlate predicted HOMO‑LUMO gaps with experimental reaction rates (n ≥ 20) using 10 000 permutations to obtain a p‑value and a 95 % confidence interval. Results are reported in `artifacts/kinetic_report.txt` and visualised in `artifacts/kinetic_correlation.png`. The analysis is explicitly labelled **exploratory** given the small sample size.  
- **Power Analysis for Correlation**: Task T034 estimates the minimum sample size needed to detect r ≈ 0.5 with 80 % power at α = 0.05. The current kinetic set falls short; the limitation is documented and the result is treated as exploratory.

### 6. Power Analysis for Paired Tests (Methodology‑bc367d3c)
- **Task T026** computes the required test‑set size for detecting a medium effect (Cohen’s d = 0.5) with 80 % power at α = 0.05 for the paired t‑test. If the scaffold split is insufficient, the split will be adjusted accordingly, and the achieved power will be logged.

### 7. Single‑Source‑of‑Truth Validation
- Run **SSoT validator** (`code/utils/ssot.py`) to ensure every figure/number in the eventual paper traces back to a single artifact; log to `artifacts/ssot.log`.

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| QM9 download failure | Exponential backoff (max 3 attempts) with clear error code; abort if all attempts fail. |
| Memory OOM during graph construction | Streamed processing; dynamic batch‑size reduction; fallback to a 10 k‑molecule sample if needed. |
| Invalid SMILES exceed 0.1 % | Log and abort; investigate source dataset integrity. |
| HOMO‑LUMO gap as a weak proxy | Provide construct‑validity justification; validate trend against kinetic dataset (permutation test) and explicitly report limitation. |
| Statistical test misuse | Use paired t‑test only for error metrics, Fisher‑Z for correlations, Bonferroni correction, and power analysis. |
| Small kinetic dataset | Perform power analysis (T034) and label results exploratory; do not over‑interpret. |

---


