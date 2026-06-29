# Data Model: Predicting Plant Defense Compound Production from Publicly Available Genomic and Transcriptomic Data

## Entity Definitions

### ExpressionMatrix

| Attribute | Type | Description | Source |
|-----------|------|-------------|--------|
| `gene_id` | string | Gene identifier (e.g., AT1G01010 for Arabidopsis) | GEO processed matrix |
| `sample_id` | string | **Biological sample identifier (unique per sample, must match MetaboliteMatrix for pairing)** | GEO metadata |
| `expression_value` | float | TPM or FPKM normalized expression | GEO processed matrix |
| `species` | string | "Arabidopsis" or "Solanum" | GEO metadata |
| `condition` | string | Treatment condition (e.g., "herbivore", "control") | GEO metadata |
| `pathway_id` | string | KEGG pathway ID (e.g., "ko00900") | KEGG mapping |
| `variance` | float | Variance across all samples | Preprocessing |

**Constraints**:
- `expression_value` ≥ 0
- `variance` ≥ 0
- `sample_id` must exist in MetaboliteMatrix for pairing

### MetaboliteMatrix

| Attribute | Type | Description | Source |
|-----------|------|-------------|--------|
| `metabolite_id` | string | Metabolite identifier (e.g., "camalexin", "glucosinolate") | Metabolomics Workbench |
| `sample_id` | string | **Biological sample identifier (must match ExpressionMatrix sample_id for pairing)** | Metabolomics Workbench |
| `concentration` | float | Log2-transformed concentration | Metabolomics Workbench |
| `pathway_class` | string | "terpenoid", "alkaloid", or "phenylpropanoid" | KEGG mapping |
| `detection_limit` | float | Instrument detection limit (if applicable) | Metabolomics Workbench |

**Constraints**:
- `concentration` can be any real number (log-transformed)
- `sample_id` must exist in ExpressionMatrix for pairing
- ≥5 samples per metabolite (spec assumption)

### FeatureSet

| Attribute | Type | Description | Source |
|-----------|------|-------------|--------|
| `gene_id` | string | Gene identifier | ExpressionMatrix subset |
| `pathway_id` | string | KEGG pathway ID | KEGG mapping |
| `species` | string | "Arabidopsis" or "Solanum" | ExpressionMatrix |
| `ortholog_of` | string | Original gene ID if ortholog substitution | Edge case handling |
| `sequence_identity` | float | Sequence identity percentage if ortholog | Edge case handling |

**Constraints**:
- All genes must map to defense pathway (terpenoid, alkaloid, phenylpropanoid)
- ≥75% of known defense pathway genes retained (SC-006)

### ModelArtifact

| Attribute | Type | Description | Source |
|-----------|------|-------------|--------|
| `model_id` | string | Unique model identifier | Pipeline run |
| `metabolite_id` | string | Target metabolite | Model training |
| `coefficients` | dict | Gene → coefficient mapping | Ridge Regression |
| `intercept` | float | Model intercept | Ridge Regression |
| `alpha` | float | Ridge penalty parameter | Model hyperparameter |
| `rmse_mean` | float | Mean RMSE across CV folds | Cross-validation |
| `rmse_std` | float | Standard deviation of RMSE | Cross-validation |
| `pearson_r_mean` | float | Mean Pearson r across CV folds | Cross-validation |
| `pearson_r_std` | float | Standard deviation of Pearson r | Cross-validation |
| `permutation_p` | float | Permutation test p-value | Permutation test |
| `permutation_p_corrected` | float | Bonferroni-corrected p-value | Multiple testing correction |

**Constraints**:
- `rmse_mean` ≥ 0
- `pearson_r_mean` ∈ [-1, 1]
- `permutation_p` ∈ [0, 1]
- `permutation_p_corrected` ≤ 1.0 (capped)

## Data Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   GEO Raw Data  │────▶│  ExpressionMatrix│────▶│  FeatureSet      │
│   (downloaded)  │     │  (normalized)    │     │  (pathway genes) │
└─────────────────┘     └──────────────────┘     └────────┬─────────┘
                                                          │
┌─────────────────────┐   ┌──────────────────┐           │
│ Metabolomics Raw    │──▶│ MetaboliteMatrix │───────────┘
│ (downloaded)        │   │ (log-transformed)│  (paired by sample_id)
└─────────────────────┘   └──────────────────┘
                                                          │
                            ┌──────────────────┐         │
                            │ Batch Correction │         │
                            │ (z-score + ComBat)│        │
                            └──────────────────┘         │
                                                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                              MODELING                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
│  │ Ridge Regression│──│ 5-Fold CV       │──│ Permutation Test    │  │
│  │ (per metabolite)│  │ (RMSE, Pearson) │  │ (1000 iterations)   │  │
│  └─────────────────┘  └─────────────────┘  └──────────┬──────────┘  │
└────────────────────────────────────────────────────────┼─────────────┘
                                                         │
                                                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                              OUTPUTS                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
│  │ ModelArtifact   │  │ cv_metrics.csv  │  │ permutation_results │  │
│  │ (coefficients)  │  │ (RMSE, r)       │  │ (p-values, corrected)│  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Validation Rules

| Rule | Entity | Condition | Error Code | Notes |
|------|--------|-----------|------------|-------|
| Sample pairing | ExpressionMatrix, MetaboliteMatrix | sample_id in both | E-PAIRING | Halt if <95% paired |
| Expression non-negative | ExpressionMatrix | expression_value ≥ 0 | E-NEGATIVE | Log and exclude |
| Pathway membership | FeatureSet | pathway_id in {terpenoid, alkaloid, phenylpropanoid} | E-PATHWAY | Log and exclude |
| Gene retention | FeatureSet | retained_genes / total_defense_genes ≥ 0.75 | E-RETENTION | Log retention rate |
| Correlation reporting | ModelArtifact | pearson_r_mean reported for all metabolites | E-CORRELATION | **Report achieved correlation; not a pass/fail threshold** |
| Significance | ModelArtifact | permutation_p_corrected ≤ 0.05 | E-SIGNIFICANCE | Bonferroni-corrected |
| Runtime | Pipeline | elapsed_time ≤ 4 hours | E-TIMEOUT | Abort if exceeded |
| Checksum match | Raw files | SHA-256 match ≥ 99% | E-CHECKSUM | All files in data/raw/ |

## File Schema Locations

| File | Schema | Location |
|------|--------|----------|
| ExpressionMatrix | expression-matrix.schema.yaml | `contracts/expression-matrix.schema.yaml` |
| MetaboliteMatrix | metabolite-matrix.schema.yaml | `contracts/metabolite-matrix.schema.yaml` |
| ModelArtifact | model-artifact.schema.yaml | `contracts/model-artifact.schema.yaml` |