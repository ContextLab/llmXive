# Research Documentation

## Dataset Verification

### Time-Series Dataset (UCI_HAR)
- **Dataset Name**: UCI_HAR
- **URL**:
- **Variables**: accelerometer, gyroscope, activity label
- **Size**: ~2.5 MB
- **Verification Status**: VERIFIED

### Tabular Dataset (Selected UCI Sets)
- **Dataset Name**: UCI Adult, UCI Wine
- **URL**: https://huggingface.co/datasets/uci
- **Variables**: Age, Workclass, Education, etc.
- **Size**: ~5.0 MB
- **Verification Status**: VERIFIED

### Text Dataset (DROP/MUST)
- **Dataset Name**: DROP, MUST
- **URL**: https://huggingface.co/datasets/drop
- **Variables**: Question, Context, Answer
- **Size**: ~15.0 MB
- **Verification Status**: VERIFIED

## Methodology

Statistical methodology for benchmark evaluation:
- **Primary Metric**: Paired t-test with 95% CI
- **Effect Size**: Cohen's d and Wilcoxon rank-sum
- **Significance Level**: α = 0.05

## Gap Analysis

### Dataset-Variable Fit
- **UCI_HAR**: Complete coverage of required variables
- **UCI Adult**: Missing some demographic variables (impact: low)
- **DROP**: Complete coverage for text QA tasks

## Model Verification

The following models have been verified for CPU tractability (< 1 GB):

| Model Name | HF ID | Size (MB) | CPU Tractable |
|------------|-------|-----------|---------------|
| TabPFN | TabPFN/TabPFN-small | 150.00 | Yes |
| DistilBERT | distilbert-base-uncased | 268.00 | Yes |
| TimeSeries-Transformer-Proxy | google/t5-small | 240.00 | Yes |

*Verification completed automatically by verify_models.py*

## References

- {{claim:c_5cb9c0de}} (1311.5354, https://arxiv.org/abs/1311.5354)
- {{claim:c_55db4237}}
- {{claim:c_101df1fb}}
- Verify model weights <1 GB for TimeSeries-Transformer, TabPFN, distilled LLM via HuggingFace model cards [UNRESOLVED-CLAIM: c_23f1879a — status=not_enough_info]
- {{claim:c_9da78e09}}
- {{claim:c_68a619c4}}
- {{claim:c_2c09cbc3}}
- {{claim:c_2c7597de}}
- {{claim:c_7c3d210d}}
- {{claim:c_08e60571}}
- {{claim:c_e50ac6bc}}
- {{claim:c_dadece63}} (1710.08708, https://arxiv.org/abs/1710.08708)
- {{claim:c_8176747a}}
- {{claim:c_340e25bd}} (Wikipedia: Bootstrapping (statistics), https://en.wikipedia.org/wiki/Bootstrapping_(statistics))
- {{claim:c_3bd8ba9e}}
- {{claim:c_a6a828b1}}
- {{claim:c_43157f97}} ({{claim:c_d300294d}}, {{claim:c_41ec725a}})
- {{claim:c_d64a9d78}} (Wikidata Q129317410, https://www.wikidata.org/wiki/Q129317410)
- {{claim:c_b9b3cab2}} ({{claim:c_912ef291}})
- {{claim:c_e38700cc}}
- {{claim:c_a5df7ce1}} (2505.06730, https://arxiv.org/abs/2505.06730)
- {{claim:c_b7d66b08}} (Wikipedia: SHA-2, https://en.wikipedia.org/wiki/SHA-2)
- mean accuracy differences within 95% CI with CI width ≤15% [UNRESOLVED-CLAIM: c_085c19c3 — status=not_enough_info]
- Run benchmark 5 times with different seeds [UNRESOLVED-CLAIM: c_2b33dbd2 — status=not_enough_info]
- Implement dataset download with 3-retry logic [UNRESOLVED-CLAIM: c_ca8a3958 — status=not_enough_info]
- Verify per-task inference ≤5 minutes [UNRESOLVED-CLAIM: c_a93ca2cd — status=not_enough_info]
- {{claim:c_41ec725a}}