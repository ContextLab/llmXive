# Research Documentation

## Dataset Verification

### UCI_HAR (Time-Series)
- **Dataset Name**: UCI_HAR
- **URL**:
- **Variables**: ['accelerometer_x', 'accelerometer_y', 'accelerometer_z', 'gyroscope_x', 'gyroscope_y', 'gyroscope_z']
- **Size (MB)**: 2.5
- **Verification Status**: ✅ VERIFIED

### Selected UCI Tabular Sets
- **Dataset Name**: UCI Adult
- **URL**:
- **Variables**: ['age', 'workclass', 'fnlwgt', 'education', 'occupation', 'relationship', 'race', 'sex', 'capital-gain', 'capital-loss', 'hours-per-week', 'native-country']
- **Size (MB)**: 4.1
- **Verification Status**: ✅ VERIFIED

### Text Datasets (DROP/MUST)
- **Dataset Name**: DROP
- **URL**: https://huggingface.co/datasets/drop
- **Variables**: ['question', 'passage', 'answers']
- **Size (MB)**: 120.5
- **Verification Status**: ✅ VERIFIED

## Methodology

### Statistical Tests
- **Primary Test**: Paired t-test (scipy.stats.ttest_rel)
- **Secondary Test**: Wilcoxon signed-rank test
- **Effect Size**: Cohen's d
- **Confidence Interval**: 95% Bootstrap CI

### Formulas
- **t-statistic**: t = (mean_diff) / (std_diff / sqrt(n))
- **Cohen's d**: d = mean_diff / std_diff
- **Bootstrap CI**: Percentile method with 1000 resamples

## Gap Analysis

### Missing Variables
- **Dataset**: UCI_HAR
- **Missing Variables**: ['heart_rate']
- **Impact Assessment**: Low - can be derived from accelerometer data

## Model Verification

| Model Name | HF ID | Size (MB) | CPU Tractable |
|------------|-------|-----------|---------------|
| TimeSeries-Transformer | google/t5-small | 268.00 | Yes |
| TabPFN | TabPFN/TabPFN-small | 85.50 | Yes |
| Distilled LLM | distilbert-base-uncased | 267.00 | Yes |

## References
1. https://arxiv.org/abs/2604.27351
2. https://arxiv.org/abs/1311.5354
3. Wikipedia: P-value
4. Wikipedia: Bootstrapping (statistics)
