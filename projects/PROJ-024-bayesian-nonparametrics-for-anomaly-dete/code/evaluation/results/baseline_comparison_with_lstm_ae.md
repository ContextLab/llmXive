# Model Comparison Summary

**Generated**: 2026-05-01T11:31:11.007218
**Models Compared**: DPGMM, ARIMA, MovingAverage, LSTM-AE
**Datasets**: electricity, traffic
**Metrics**: f1_score, precision, recall, auc

## Best Overall Performance
- **Model**: DPGMM
- **Metric**: auc
- **Score**: 0.8800

## Statistical Tests (Bonferroni-corrected)
| Model A | Model B | Metric | Statistic | P-value | Significant | Effect Size |
|---------|---------|--------|-----------|---------|-------------|-------------|
| DPGMM | ARIMA | f1_score | 22.1359 | 0.0000 | ✓ | 9.8995 |
| DPGMM | ARIMA | precision | 13.4164 | 0.0002 | ✓ | 6.0000 |
| DPGMM | ARIMA | recall | 17.8885 | 0.0001 | ✓ | 8.0000 |
| DPGMM | ARIMA | auc | 15.6525 | 0.0001 | ✓ | 7.0000 |
| DPGMM | ARIMA | f1_score | inf | 0.0000 | ✓ | 8000000.0000 |
| DPGMM | ARIMA | precision | 2570676529622780.0000 | 0.0000 | ✓ | 6999999.9574 |
| DPGMM | ARIMA | recall | 3305155538086431.0000 | 0.0000 | ✓ | 8999999.9452 |
| DPGMM | ARIMA | auc | inf | 0.0000 | ✓ | 9000000.0000 |
| DPGMM | MovingAverage | f1_score | 37.9473 | 0.0000 | ✓ | 16.9705 |
| DPGMM | MovingAverage | precision | 24.5967 | 0.0000 | ✓ | 11.0000 |
| DPGMM | MovingAverage | recall | 29.0689 | 0.0000 | ✓ | 13.0000 |
| DPGMM | MovingAverage | auc | 26.8328 | 0.0000 | ✓ | 12.0000 |
| DPGMM | MovingAverage | f1_score | inf | 0.0000 | ✓ | 13000000.0000 |
| DPGMM | MovingAverage | precision | 5362586730978793.0000 | 0.0000 | ✓ | 11999999.9400 |
| DPGMM | MovingAverage | recall | inf | 0.0000 | ✓ | 14000000.0000 |
| DPGMM | MovingAverage | auc | inf | 0.0000 | ✓ | 14000000.0000 |
| DPGMM | LSTM-AE | f1_score | 9.4868 | 0.0007 | ✓ | 4.2426 |
| DPGMM | LSTM-AE | precision | 4.4721 | 0.0111 | ✗ | 2.0000 |
| DPGMM | LSTM-AE | recall | 8.9443 | 0.0009 | ✓ | 4.0000 |
| DPGMM | LSTM-AE | auc | 4.4721 | 0.0111 | ✗ | 2.0000 |
| DPGMM | LSTM-AE | f1_score | inf | 0.0000 | ✓ | 4000000.0000 |
| DPGMM | LSTM-AE | precision | 1103062345493485.1250 | 0.0000 | ✓ | 2999999.9818 |
| DPGMM | LSTM-AE | recall | inf | 0.0000 | ✓ | 5000000.0000 |
| DPGMM | LSTM-AE | auc | 1468958016927301.2500 | 0.0000 | ✓ | 3999999.9756 |
| ARIMA | MovingAverage | f1_score | inf | 0.0000 | ✓ | 5000000.0000 |
| ARIMA | MovingAverage | precision | inf | 0.0000 | ✓ | 5000000.0000 |
| ARIMA | MovingAverage | recall | 1836197521159127.2500 | 0.0000 | ✓ | 4999999.9696 |
| ARIMA | MovingAverage | auc | 1836197521159128.2500 | 0.0000 | ✓ | 4999999.9696 |
| ARIMA | MovingAverage | f1_score | inf | 0.0000 | ✓ | 5000000.0000 |
| ARIMA | MovingAverage | precision | 1836197521159128.2500 | 0.0000 | ✓ | 4999999.9696 |
| ARIMA | MovingAverage | recall | 1836197521159128.2500 | 0.0000 | ✓ | 4999999.9696 |
| ARIMA | MovingAverage | auc | inf | 0.0000 | ✓ | 5000000.0000 |
| ARIMA | LSTM-AE | f1_score | -1800560885367232.2500 | 0.0000 | ✓ | -3999999.9801 |
| ARIMA | LSTM-AE | precision | -1800560885367229.2500 | 0.0000 | ✓ | -3999999.9801 |
| ARIMA | LSTM-AE | recall | -inf | 0.0000 | ✓ | -4000000.0000 |
| ARIMA | LSTM-AE | auc | -1836197521159127.2500 | 0.0000 | ✓ | -4999999.9696 |
| ARIMA | LSTM-AE | f1_score | -inf | 0.0000 | ✓ | -4000000.0000 |
| ARIMA | LSTM-AE | precision | -inf | 0.0000 | ✓ | -4000000.0000 |
| ARIMA | LSTM-AE | recall | -1468958016927301.2500 | 0.0000 | ✓ | -3999999.9756 |
| ARIMA | LSTM-AE | auc | -1836197521159128.2500 | 0.0000 | ✓ | -4999999.9696 |
| MovingAverage | LSTM-AE | f1_score | -4021940048234096.5000 | 0.0000 | ✓ | -8999999.9550 |
| MovingAverage | LSTM-AE | precision | -4021940048234094.0000 | 0.0000 | ✓ | -8999999.9550 |
| MovingAverage | LSTM-AE | recall | -3305155538086431.0000 | 0.0000 | ✓ | -8999999.9452 |
| MovingAverage | LSTM-AE | auc | -inf | 0.0000 | ✓ | -10000000.0000 |
| MovingAverage | LSTM-AE | f1_score | -inf | 0.0000 | ✓ | -9000000.0000 |
| MovingAverage | LSTM-AE | precision | -3305155538086432.0000 | 0.0000 | ✓ | -8999999.9452 |
| MovingAverage | LSTM-AE | recall | -inf | 0.0000 | ✓ | -9000000.0000 |
| MovingAverage | LSTM-AE | auc | -3672395042318258.0000 | 0.0000 | ✓ | -9999999.9391 |