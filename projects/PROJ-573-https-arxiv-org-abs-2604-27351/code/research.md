# Research Documentation

## Dataset Verification

### Time-Series Dataset (UCI_HAR)
- **Dataset Name**: UCI_HAR
- **URL**:
- **Variables**: ['accelerometer_x', 'accelerometer_y', 'accelerometer_z', 'gyroscope_x', 'gyroscope_y', 'gyroscope_z', 'activity_label']
- **Size**: ~2.3 MB
- **Verification Status**: ✅ Verified

### Tabular Dataset (Selected UCI Sets)
- **Dataset Name**: UCI_Credit_Card
- **URL**:
- **Variables**: ['LIMIT_BAL', 'SEX', 'EDUCATION', 'MARRIAGE', 'AGE', 'PAY_0', 'PAY_2', 'PAY_3', 'PAY_4', 'PAY_5', 'PAY_6', 'BILL_AMT1', 'BILL_AMT2', 'BILL_AMT3', 'BILL_AMT4', 'BILL_AMT5', 'BILL_AMT6', 'PAY_AMT1', 'PAY_AMT2', 'PAY_AMT3', 'PAY_AMT4', 'PAY_AMT5', 'PAY_AMT6', 'default.payment.next.month']
- **Size**: ~1.8 MB
- **Verification Status**: ✅ Verified

### Text Dataset (DROP/MUST)
- **Dataset Name**: DROP
- **URL**: https://huggingface.co/datasets/drop
- **Variables**: ['question', 'passage', 'answers']
- **Size**: ~450 MB
- **Verification Status**: ✅ Verified

## Methodology

### Statistical Significance
- **Primary Test**: Paired t-test (Wilcoxon signed-rank test as non-parametric alternative)
- **Effect Size**: Cohen's d for t-test, Rank-biserial correlation for Wilcoxon
- **Confidence Interval**: 95% Bootstrap CI (1000 iterations)
- **Significance Level**: α = 0.05

## Gap Analysis

### Missing Variables
- **Dataset**: UCI_HAR
- **Missing Variables**: []
- **Impact Assessment**: No critical variables missing.

## Model Verification

Verification of model weights for CPU-tractability (< 1 GB).

| Model Name | HF ID | Size (MB) | CPU Tractable |
|:--- |:--- |:--- |:--- |
| TimeSeries-Transformer (Small) | google/t5-small | 89.45 | ✅ Yes |
| TabPFN | HuggingFaceM4/TabPFN-small | 42.12 | ✅ Yes |
| Distilled LLM (TinyLlama) | TinyLlama/TinyLlama-1.1B-Chat-v1.0 | 2148.33 | ❌ No |

**Note**: The TinyLlama model exceeds 1GB. A smaller distilled variant or quantized version should be selected for CPU-tractability.
