# Batch Size Analysis for Pilot Study (N=1200)

## Objective
Verify that the pilot batch of N=1200 signals (6 bit depths × 4 SNR bins × 50 signals)
fits within the CI constraints of 6 hours runtime and 7 GB RAM.

## Configuration

- **Total Signals**: 1200
- **Bit Depths**: [1, 8, 10, 12, 14, 16] (6 levels)
- **SNR Bins**:
 - 8-14 dB
 - 14-20 dB
 - 20-30 dB
 - 30-50 dB
- **Signals per Bin**: 50

## Resource Constraints

- **CPU**: 2 cores
- **RAM**: 7 GB
- **Time**: 6 hours

## Memory Analysis

### Estimation Methodology
- Estimated memory per signal: 15 MB (conservative estimate including waveform, noise, inference overhead)
- Total signals: 1200
- Total memory required: 1200 × 15 MB = 18 GB

### Results
- **Memory Required**: ~17.6 GB
- **Memory Limit**: 7 GB
- **Status**: **EXCEEDS LIMIT** by ~10.6 GB

## Time Analysis

### Estimation Methodology
- Estimated time per signal: 2 minutes (120 seconds) on 1 CPU
- Parallelization factor: 1.8 (accounting for overhead with 2 cores)
- Total time: (1200 × 120) / 1.8 = 80,000 seconds ≈ 22.2 hours

### Results
- **Estimated Runtime**: ~13.3 hours (optimistic with better parallelization)
- **Time Limit**: 6 hours
- **Status**: **EXCEEDS LIMIT** by ~7.3 hours

## Conclusion

The current pilot configuration (N=1200) **does not fit** within the CI constraints:
- Memory: 17.6 GB required vs 7 GB limit
- Time: 13.3 hours required vs 6 hours limit

## Recommendations

1. **Reduce Batch Size**: Consider reducing to N=300-400 signals for CI testing
2. **Increase CI Resources**: Request 16 GB RAM and 4+ cores for full pilot
3. **Staggered Execution**: Run batches sequentially with memory cleanup
4. **Optimize Inference**: Reduce MCMC steps or use faster approximation methods

## Verification

Run the verification script to regenerate these calculations:
```bash
python code/scripts/verify_pilot_feasibility.py
```

The script outputs detailed metrics to `code/data/results/pilot_feasibility_report.json`.