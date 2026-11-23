# Scientific Methodology

## 1. Objective
To quantify the robustness of common statistical tests (Student's t-test, ANOVA, Chi-squared) to violations of the independence assumption.

## 2. Hypothesis
As the strength of dependency ($r$) increases, the observed Type I error rate will significantly exceed the nominal alpha level ($\alpha = 0.05$), and statistical power will decrease when true effects are present.

## 3. Experimental Design

### 3.1. Dependency Injection Methods
We simulate three types of non-independence:
1. **Temporal (AR(1))**: Data points are generated with autocorrelation $r$.
 $$x_t = r \cdot x_{t-1} + \epsilon_t$$
2. **Hierarchical (Block Bootstrap)**: Data is resampled in blocks of size $\sqrt{N}$ to simulate cluster effects.
3. **Spatial (Kernel Smoothing)**: Dependency is introduced based on feature-space proximity using a Gaussian kernel.

### 3.2. Null Hypothesis Construction
Two distinct paradigms are used to ensure scientific validity:

#### A. Synthetic Data (Generate-then-Inject)
1. Generate data $X$ under true independence ($r=0$).
2. Inject dependency structure with strength $r$.
3. Since the ground truth is known (no effect), any rejection of $H_0$ is a Type I error.

#### B. Real Data (Inject-then-Permute)
1. Load real dataset $D$.
2. Inject dependency structure with strength $r$ into the features.
3. **Permute the target variable** $Y$ randomly to break any existing correlation between $X$ and $Y$.
4. This creates a valid null hypothesis on real-world feature distributions. Any rejection is a Type I error.

### 3.3. Statistical Tests
- **t-test**: For binary classification targets with continuous features.
- **ANOVA**: For multi-class targets with continuous features.
- **Chi-squared**: For categorical targets and categorical features (or binned continuous features using Sturges' rule).

## 4. Metrics

### 4.1. Type I Error Rate
$$ \text{Type I Error} = \frac{\text{Count}(p < \alpha)}{\text{Total Replications}} $$
Confidence intervals are calculated using the **Clopper-Pearson** method to ensure rigorous bounds.

### 4.2. Statistical Power
$$ \text{Power} = \frac{\text{Count}(p < \alpha | \text{True Effect})}{\text{Total Replications}} $$
Power is measured by injecting a true effect (mean shift $\delta = 1.0\sigma$) before dependency injection.

### 4.3. Trend Verification
Monotonicity of error rate increase with $r$ is verified using:
- **Spearman Rank Correlation**
- **Mann-Kendall Trend Test** (non-parametric)

## 5. Data Integrity
- **No Synthetic Input**: All real datasets are fetched from verified UCI URLs.
- **Fail-Loud Policy**: If a dataset fetch fails, the pipeline halts. No synthetic fallback is permitted for real data runs.
- **Validation**: All datasets are validated for $N \ge 50$ and sufficient variance/levels before inclusion.

## 6. Reproducibility
- All random seeds are pinned in `code/config.yaml`.
- Full parameter sets are logged in `results/config_audit.json`.
- Code is versioned and deterministic.
