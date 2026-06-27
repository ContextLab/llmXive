#!/usr/bin/env python3
"""McNemar's test for human alignment study and ablation results significance."""

import numpy as np
from scipy.stats import chi2
import argparse
import json

def mcnemar_test(confusion_matrix):
    """Perform McNemar's test on a 2x2 contingency table.

    Args:
        confusion_matrix: 2x2 array where:
            [[a, b],
             [c, d]]
            a = both methods correct, b = method1 correct only
            c = method2 correct only, d = both methods incorrect

    Returns:
        chi2_stat: Chi-squared test statistic (with continuity correction)
        p_value: p-value from chi2 distribution with df=1
    """
    b, c = confusion_matrix[0, 1], confusion_matrix[1, 0]
    
    # McNemar's chi-squared statistic with continuity correction
    if b + c > 0:
        chi2_stat = (abs(b - c) - 1) ** 2 / (b + c)
    else:
        chi2_stat = 0.0
    
    p_value = 1 - chi2.cdf(chi2_stat, df=1)
    
    return chi2_stat, p_value

def main():
    parser = argparse.ArgumentParser(description='McNemar\'s test for significance')
    parser.add_argument('--data', type=str, required=True,
                        help='JSON file with contingency table data')
    parser.add_argument('--output', type=str, required=True,
                        help='Output JSON file with test results')
    args = parser.parse_args()

    with open(args.data, 'r') as f:
        data = json.load(f)

    results = {}
    for study_name, cm in data.items():
        cm = np.array(cm)
        chi2_stat, p_value = mcnemar_test(cm)
        results[study_name] = {
            'chi2_statistic': float(chi2_stat),
            'p_value': float(p_value),
            'significant_at_0.05': p_value < 0.05
        }

    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)

    print(json.dumps(results, indent=2))

if __name__ == '__main__':
    main()
