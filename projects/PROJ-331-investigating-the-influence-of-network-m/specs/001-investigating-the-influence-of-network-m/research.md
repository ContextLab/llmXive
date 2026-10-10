# Research: Investigating the Influence of Network Motifs on Resting-State Functional Connectivity

## 1. Research Question & Hypothesis

**Question**: Do specific 3-node and 4-node network motif configurations in structural brain connectomes *associate* with (not constrain — observational, associational framing) individual variation in rsFC strength and global efficiency?

**Hypothesis**: Motif z-scores (prevalence vs. degree-preserving nulls) for particular motifs associate with rsFC strength and/or global efficiency across subjects, after controlling for structural global degree.

## 2. Dataset Strategy

| Dataset | Source | Access Method | Variables Used | Verification Status |
|---------|--------|---------------|----------------|---------------------|
| OpenNeuro preprocessed fMRI (fsLR-64k) | https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00000-of-00016.parquet (dataset dict: https://huggingface.co/datasets/clane9/openneuro-fslr64k.arrow/resolve/main/dataset_dict.json) | Direct parquet download / `datasets` streaming | Resting-state BOLD-derived surface time series → rsFC matrices | ✅ Verified open download |
| OpenNeuro ds001734 (named in spec) | No verified source found | — | Diffusion + rs-fMRI pairing | ❌ No verified URL; described by name only, NOT citable as a download |
| HCP structural connectomes (named in constitution Principle VI) | Access-gated (registration/DUA) | — | Diffusion tractography | ❌ Cannot be fetched on CI; no open substitute verified |

**Dataset–variable fit assessment (blocking finding)**: The study requires *paired* diffusion tractography and rs-fMRI per subject. The only verified source (the fsLR-64k parquet) contains functional data but **no diffusion tractography**, so structural connectomes — the core predictor — cannot be derived from any verified open source. Per the plan's anti-fabrication rules, no synthetic structural stand-in is used. The motif-analysis code is implemented and unit-tested on labeled test graphs; the motif–rsFC association stage is gated on real structural data and reports the gap honestly if unavailable. This is a scope mismatch requiring spec-level correction (name a verified open diffusion dataset, or reframe the question).

## 3. Methodology

### 3.1 Data acquisition & preprocessing
1. Stream/download the verified parquet; select up to 50 subjects with usable resting-state runs; checksum raw files under `data/raw/`.
2. Parcellate BOLD time series to a 100-node cortical parcellation (Schaefer-100 mapping applied to fsLR vertices); compute Pearson rsFC → `rsfc.npy`.
3. rsFC strength = mean absolute off-diagonal correlation; global efficiency computed on the thresholded (|r| > 0.2) weighted graph via `networkx.global_efficiency` on the binarized thresholded graph.
4. Missing runs → warning + subject skip (FR-001 acceptance 2).

### 3.2 Motif quantification (gated on real structural input)
- Undirected binary graphs; enumerate all 3-node (4 non-isomorphic) and 4-node motif classes via `networkx` subgraph isomorphism counting (GF enumeration), covering the 13 motif categories the spec tests.
- Null model: Maslov–Sneppen degree-preserving rewiring, ≥1000 iterations, seed 42; z = (N_obs − μ_null)/σ_null; σ=0 → z=0 (disconnected/absent motifs, per US-2 acceptance 2).
- 300 s wall-clock guard per subject (SC-002): abort gracefully with timeout warning.

### 3.3 Statistical analysis
- Partial Pearson and Spearman correlations of each motif z-score with each metric (strength, global efficiency), controlling for structural global degree.
- Bonferroni across the 13 tested motifs (α_adj = 0.05/13 ≈ 0.00385); flag corrected p < 0.05.
- VIF over the full motif predictor set; VIF ≥ 5 → warning logged, all motifs still tested (per FR-005); pairwise Pearson correlations among predictors, flag |r| ≥ 0.9, still report all p-values.
- Permutation test: ≥1000 label shuffles, seed 42, empirical p per motif.
- Zero-variance motif vectors (var < 1e-6) → skip test, record "insufficient variance".
- Power analysis: minimum detectable Pearson r for N = 50, α = 0.05/13, power = 0.80 (power value 0.80 per Wikipedia, "Power (statistics)"), reported with Type II error implications.
- **Causal framing**: observational, cross-sectional — associational claims only; enforced by the FR-009 disclaimer.
- **Power limitation**: N = 50 with α_adj ≈ 0.00385 yields a large minimum detectable r; acknowledged explicitly rather than claiming adequate power.

### 3.4 Reporting
- `results.pdf`: per-motif pages (scatter + 95% CI band, partial r's, raw/Bonferroni/empirical p, VIF, pairwise predictor correlations), power section, limitations (including the structural-data gap if gated), and the exact disclaimer string "These findings are associational only and do not imply causation." verified by PDF text extraction.

## 4. Compute Feasibility

- **CPU-first**: every method (parquet streaming, Pearson correlation, motif enumeration on 100-node graphs, Maslov–Sneppen nulls, permutations, PDF generation) runs faithfully on the 2-core/7 GB runner. No GPU escape hatch needed.
- Motif enumeration: 100-node graphs, ~10⁶ triplets/quadruplets with vectorized counting — well under 300 s.
- Permutations: 1000 × 13 tests, NumPy-vectorized — minutes.
- Data: stream the parquet shard-by-shard; only derived matrices (50 × ~40 KB) persist — far under disk/RAM limits.

## 5. Decision / Rationale

- **rs-fMRI source**: the verified OpenNeuro fsLR-64k parquet is the only programmatically downloadable OpenNeuro mirror available; used for the functional modality.
- **Structural modality**: no verified open diffusion source exists (ds001734 unverified; HCP gated). Rather than fabricate synthetic connectomes (rejected — a simulated stand-in for real brain structure would be fabrication), the structural stages are gated and the mismatch surfaced for spec revision.
- **Statistics**: Bonferroni chosen per spec; permutation test as robustness; VIF/pairwise diagnostics per FR-005; power analysis per FR-010 with honest limitation statement.
- **Motif scope**: 3- and 4-node motifs only (spec assumption); undirected binary treatment consistent with standard motif practice (Milo et al.; no verified URL available, cited by name only).
