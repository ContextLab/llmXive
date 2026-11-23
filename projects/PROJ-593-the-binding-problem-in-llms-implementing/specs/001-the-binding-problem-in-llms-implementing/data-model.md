# Data Model: The Binding Problem in LLMs – Synchronized Oscillations for Feature Integration

## 1. Overview
Defines all raw, intermediate, and final data artifacts. Every artifact is version‑controlled, checksummed, and validated against the JSON‑Schema contracts.

## 2. Raw Data Sources
| Source | Verified URL | Format | Key Fields |
|--------|--------------|--------|------------|
| **Synthetic PLV Reference** | ` | JSON | `signal`, `phase`, `frequency` |
| **CLUTRR** | ` | Parquet | `story`, `question`, `answer`, `family_size` |
| **bAbI‑style QA** | ` | JSONL | `question`, `answer` |

All raw files are streamed where possible; SHA‑256 checksums are stored in `state/projects/PROJ-593...yaml`.

## 3. Intermediate Data Structures
| Artifact | Description | Shape / Type | Storage |
|----------|-------------|--------------|---------|
| **ActivationTimeSeries** | Raw attention‑head outputs (after sinusoidal gating) | `(batch, layer, head, seq_len)` – `np.ndarray` (`float32`) | `data/processed/activations_{seed}.npy` |
| **ResidualPhaseSeries** | Instantaneous phase of activations after subtracting deterministic mask | `np.ndarray` (`float32`) per head | `data/processed/residual_phase_{seed}.npy` |
| **SpectralFeatures** | Welch PSD per head, plus SNR | dict: `frequency_band`, `psd` (`np.ndarray`), `snr` (`float`) | `data/processed/spectral_{seed}.json` |
| **PLVSeries** | Sliding‑window PLV between model residual phase and synthetic reference phase | `np.ndarray` (`float32`) per frequency | `data/processed/plv_{freq}_{seed}.npy` |
| **BenchmarkResult** | Accuracy & F1 for each seed and task | `accuracy` (`float`), `f1_score` (`float`), `seed` (`int`) | `data/processed/benchmark_{task}_{seed}.json` |
| **PermutationTestResult** | Null distribution & observed PLV statistic | `null_distribution` (`list[float]`), `observed_value` (`float`), `p_value` (`float`) | `data/processed/permutation_{freq}.json` |

## 4. Output Schema
### 4.1 `results_summary.json`
```json
{
  "frequency_sweep": [
    {
      "frequency_hz": 40,
      "mean_snr": 3.2,
      "mean_plv": 0.42,
      "p_value": 0.018,
      "significance": true
    }
    // … one entry per tested frequency
  ],
  "benchmark_performance": {
    "clutrr": {"accuracy": 0.78, "f1_score": 0.75, "p_value": 0.032},
    "babi":   {"accuracy": 0.81, "f1_score": 0.79, "p_value": 0.027}
  }
}
```

### 4.2 `statistical_report.json`
```json
{
  "permutation_test": {
    "n_permutations": 1000,
    "null_distribution": [...],
    "observed_value": 0.42,
    "p_value": 0.018
  },
  "correction_method": "bonferroni",
  "assumptions": [
    "Associational Similarity",
    "Exogenous Oscillatory Constraint"
  ]
}
```

All final JSON files are validated against `contracts/output.schema.yaml`.

## 5. Data Hygiene & Versioning
- **Checksums**: Computed with `sha256sum` after each download; recorded in `state/...yaml`.  
- **Derivation**: Raw → processed files are never overwritten; each step writes a new file with a timestamped suffix.  
- **PII**: All datasets are anonymised; no personal identifiers are stored.

---

