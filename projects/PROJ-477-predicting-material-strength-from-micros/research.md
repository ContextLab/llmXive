# Research Notes: Predicting Material Strength from Microstructure Images

## Executive Summary
This document tracks the research decisions, data sources, and methodological choices for the
PROJ-477 project. It is updated as the pipeline evolves.

## Data Sources

### Primary Dataset
- **Source**: HuggingFace Datasets (`material-science/ebsd-microstructures`)
- **Access**: Programmatically downloaded via `code/data/download.py`
- **Checksum**: SHA-256 verification performed on download
- **License**: Open Data Commons License

### Verification
The dataset was verified against the HuggingFace repository manifest. All images and
associated metadata were successfully downloaded and checksums matched.

## Data Labeling Strategy

### Protocol
Labels (Yield Strength in MPa) are generated using the **Hall-Petch relationship**, a
fundamental physics-based model in materials science. This approach ensures that the
target variable is physically meaningful and consistent with metallurgical theory.

**Formula**:
```
σ_y = σ_0 + k_y * d^(-0.5)
```
Where:
- `σ_y`: Yield Strength (MPa)
- `σ_0`: Friction stress (baseline resistance, ~100 MPa for steel)
- `k_y`: Hall-Petch slope (material constant, ~0.5 MPa·m^0.5)
- `d`: Average grain size (micrometers, converted to meters for calculation)

**Implementation**:
1. Grain size is extracted from EBSD images using `code/data/extract_features.py`.
2. Features are stored in `data/processed/grain_features.csv`.
3. The `code/data/label_generator.py` module applies the Hall-Petch formula to generate
 the `yield_strength_mpa` column for the training manifest.
4. Constants `σ_0` and `k_y` are configurable via `code/utils/config.py` but default to
 standard values for low-carbon steel.

**Rationale**:
Direct experimental measurement of yield strength for every microstructure image is
cost-prohibitive and time-consuming. The Hall-Petch relationship provides a robust,
theoretically grounded proxy that correlates strongly with microstructural grain size.
This allows the CNN to learn the visual features associated with mechanical strength
without requiring a massive experimental dataset.

### Power Analysis Status
- **Status**: Completed
- **Effect Size**: Medium (Cohen's d = 0.5) assumed based on prior literature in
 microstructure-property modeling.
- **Power Target**: 0.80 (80%)
- **Significance Level (α)**: 0.05
- **Calculated Sample Size**: Minimum 64 images per split (Train/Val/Test) required.
- **Actual Sample Size**: The downloaded dataset contains 1,200 unique microstructure
 images, providing ample statistical power (>0.99) to detect medium effect sizes
 between the CNN model and the baseline predictor.
- **Conclusion**: The dataset size is sufficient to reject the null hypothesis if the
 CNN model provides a statistically significant improvement over the Hall-Petch baseline.
 The `code/eval/metrics.py` module implements a single-sample t-test on squared errors
 to verify this significance during evaluation.

## Model Architecture Decisions

### Backbone Selection
- **Model**: MobileNetV2 (pretrained on ImageNet)
- **Rationale**: Lightweight architecture suitable for CPU inference. The feature
 extraction layers are frozen to prevent overfitting on the relatively small dataset.
- **Head**: Custom regression head (Linear layers) mapping the 1280-dim bottleneck to
 a single scalar (Yield Strength).

### Training Strategy
- **Optimizer**: AdamW
- **Loss**: Mean Squared Error (MSE)
- **Augmentation**: Random rotation, horizontal flip, and brightness jitter applied
 during training to improve generalization (see `code/train/augment.py`).

## Evaluation Metrics

- **Primary**: Mean Squared Error (MSE), R² Score
- **Secondary**: Statistical significance (p-value) comparing CNN error vs. Baseline error
- **Null Hypothesis**: If R² < 0.2, the model is considered to have failed to learn
 meaningful features beyond a trivial baseline (see `code/eval/evaluator.py`).

## Future Work

- Investigate transfer learning from other materials science datasets.
- Incorporate multi-modal data (e.g., XRD patterns) if available.
- Extend to multi-class classification (e.g., brittle vs. ductile failure modes).