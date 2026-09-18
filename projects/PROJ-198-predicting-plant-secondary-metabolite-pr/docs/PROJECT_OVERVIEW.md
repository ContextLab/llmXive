# Project Overview: Predicting Plant Secondary Metabolite Profiles

## Scientific Goal

To establish a predictive relationship between genomic features (specifically Biosynthetic Gene Clusters - BGCs) and secondary metabolite profiles in plants, accounting for phylogenetic non-independence.

## Methodology

### 1. Data Acquisition & Alignment
- **Genomic Data**: Downloaded from NCBI RefSeq or Phytozome. Filtered by genome size (< 500MB).
- **Metabolite Data**: Retrieved from PMDB/MetaboLights. Normalized via InChIKey.
- **BGC Detection**: antiSMASH pipeline executed on genomic assemblies.
- **Mapping**: BGC types mapped to metabolite classes using MIBiG ontology and Pfam HMMs for plant-specific clusters.

### 2. Feature Engineering
- **BGC Features**: Binary presence/absence and count matrices.
- **Metabolite Features**: Log-transformed abundance (+1 pseudo-count).
- **Dimensionality Reduction**: PCA applied to high-dimensional metabolite features before modeling.

### 3. Predictive Modeling
- **Primary Model**: Phylogenetic Generalized Least Squares (PGLS) using a covariance matrix derived from species tree.
- **Secondary Models**: Random Forest, Elastic Net, Gradient Boosting (with LOO or 5-fold CV).
- **Baseline**: Phylogenetic permutation test to establish null R².

### 4. Validation & Sensitivity
- **Robustness Check**: Sensitivity sweep across BGC detection thresholds (0.1, 0.3, 0.5, 0.7).
- **Success Criteria**: R² variation ≤ 0.05 across thresholds.

## Pipeline Architecture

```
[Raw Data] -> [Download] -> [Preprocess] -> [Align] -> [Model] -> [Report]
 | | | | | |
 v v v v v v
Genomes antiSMASH Harmonize Matrix PGLS/RF Markdown
Metabolites Mapping Log-trans Output Sensitivity Metrics
```

## Key Modules

- `code/data/download.py`: Network I/O, retry logic, source fallback.
- `code/data/preprocess.py`: antiSMASH wrapper, InChIKey normalization, MIBiG mapping.
- `code/data/align.py`: Merging genomic and metabolomic data by species.
- `code/modeling/phylo.py`: Tree loading, covariance matrix construction, PGLS training.
- `code/modeling/train.py`: PCA, stratified splitting, model training loops.
- `code/modeling/eval.py`: Metric calculation, permutation baseline, sensitivity sweep.
- `code/utils/report.py`: Report generation and formatting.

## Output Artifacts

1. `data/processed/aligned_matrix.csv`: Final feature matrix.
2. `data/processed/metrics.json`: Model performance metrics.
3. `data/processed/sensitivity_results.json`: Threshold sweep results.
4. `data/processed/final_report.md`: Human-readable summary.

## Compliance

- **Constitution Principle III**: Runtime schema validation via Pydantic.
- **Constitution Principle V**: Data hygiene via checksums and state tracking.
- **FR-010**: PGLS as primary analysis.
- **SC-002**: Sensitivity analysis for robustness.
- **SC-004**: Alignment success rate logging.
