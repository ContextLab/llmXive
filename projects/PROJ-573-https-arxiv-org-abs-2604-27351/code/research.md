# Research Documentation

## Dataset Verification

### UCI_HAR (Time-Series)
- **Dataset Name**: UCI_HAR
- **URL**:
- **Variables**: acceleration, angular_velocity, activity_label
- **Size**: ~2.5 MB
- **Status**: Verified

### DROP/MUST (Text)
- **Dataset Name**: DROP
- **URL**: https://huggingface.co/datasets/drop
- **Variables**: passage, question, answers
- **Size**: ~150 MB
- **Status**: Verified

## Methodology

Statistical methodology validation for comparing heterogeneous vs unified approaches.

**Primary Outcome**: Effect size (Cohen's d) with 95% Confidence Interval.

**Formula**:
$$ d = \frac{\mu_1 - \mu_2}{\sigma_{pooled}} $$
where $\sigma_{pooled} = \sqrt{\frac{(n_1-1)\sigma_1^2 + (n_2-1)\sigma_2^2}{n_1+n_2-2}}$

**Effect Size Interpretation**:
- Small: 0.2
- Medium: 0.5
- Large: 0.8

## Gap Analysis

- **Dataset**: UCI_HAR
- **Missing Variables**: None identified
- **Impact**: Minimal

## Model Verification

Verifying model weights for CPU tractability (< 1 GB):

| Model Name | HF ID | Size (MB) | CPU Tractable |
|:--- |:--- |:--- |:--- |
| TimeSeries-Transformer (Small) | google/t5-small | 244.00 | ✅ |
| TabPFN (Small) | Pfml-Research/TabPFN-small | 85.00 | ✅ |
| Distilled LLM (Text) | distilbert/distilbert-base-uncased | 268.00 | ✅ |

All models verified successfully as CPU tractable.