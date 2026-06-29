"""
Contract test for the bug‑label reliability validation script.

The test creates a tiny synthetic dataset, writes it to a temporary CSV
file, invokes :func:`code.data.validate_bug_labels.validate_bug_labels`,
and checks that the returned dictionary conforms to the expected contract:

* It must be a ``dict``.
* It must contain the keys ``precision``, ``recall`` and ``f1_score``.
* All values must be ``float`` objects in the range ``[0.0, 1.0]``.
* The numeric values must match the manually computed metrics.
"""

import math
import pandas as pd
import pytest

from code.data.validate_bug_labels import validate_bug_labels


@pytest.mark.parametrize(
    "true_labels,pred_labels,expected",
    [
        # Simple case with some TP, FP, FN
        (
            [1, 0, 1, 0, 1],
            [1, 0, 0, 0, 1],
            {
                "precision": 2 / (2 + 0),  # TP=2, FP=0
                "recall": 2 / (2 + 1),    # TP=2, FN=1
            },
        ),
        # All correct
        (
            [0, 1, 0, 1],
            [0, 1, 0, 1],
            {"precision": 1.0, "recall": 1.0},
        ),
        # No positives predicted
        (
            [1, 1, 0, 0],
            [0, 0, 0, 0],
            {"precision": 0.0, "recall": 0.0},
        ),
    ],
)
def test_validate_bug_labels_contract(tmp_path, true_labels, pred_labels, expected):
    # Build a DataFrame with the required columns
    df = pd.DataFrame(
        {"bug_label": true_labels, "predicted_label": pred_labels}
    )
    csv_path = tmp_path / "labels.csv"
    df.to_csv(csv_path, index=False)

    # Run the validation script
    result = validate_bug_labels(str(csv_path))

    # Basic contract checks
    assert isinstance(result, dict), "Result must be a dict"
    for key in ("precision", "recall", "f1_score"):
        assert key in result, f"Missing key '{key}' in result"
        value = result[key]
        assert isinstance(value, float), f"Value for '{key}' must be float"
        assert 0.0 <= value <= 1.0, f"Value for '{key}' out of range [0, 1]"

    # Compute expected precision/recall manually
    tp = sum(
        1
        for t, p in zip(true_labels, pred_labels)
        if t == 1 and p == 1
    )
    fp = sum(
        1
        for t, p in zip(true_labels, pred_labels)
        if t == 0 and p == 1
    )
    fn = sum(
        1
        for t, p in zip(true_labels, pred_labels)
        if t == 1 and p == 0
    )
    exp_precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    exp_recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    exp_f1 = (
        (2 * exp_precision * exp_recall) / (exp_precision + exp_recall)
        if (exp_precision + exp_recall) > 0
        else 0.0
    )

    # Verify numeric values against expected ones (allow tiny tolerance)
    assert math.isclose(
        result["precision"], exp_precision, rel_tol=1e-9
    ), "Precision does not match expected value"
    assert math.isclose(
        result["recall"], exp_recall, rel_tol=1e-9
    ), "Recall does not match expected value"
    assert math.isclose(
        result["f1_score"], exp_f1, rel_tol=1e-9
    ), "F1 score does not match expected value"