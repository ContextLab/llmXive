import pytest
from code.data.generator_logic import generate_all_traces, FailureType

def test_generate_all_traces_returns_ten():
    traces = generate_all_traces()
    assert len(traces) == 10, "Exactly ten traces should be generated"

def test_trace_labels_are_correct():
    traces = generate_all_traces()
    # Count occurrences of each failure type
    label_counts = {
        FailureType.STATE_PERSISTENCE_ERROR: 0,
        FailureType.REASONING_DEFICIT: 0,
        FailureType.PASS: 0,
    }
    for trace in traces:
        label = trace.ground_truth_label
        # Convert string label back to enum for counting
        enum_label = None
        for ft in FailureType:
            if ft.value == label:
                enum_label = ft
                break
        assert enum_label is not None, f"Unexpected label {label}"
        label_counts[enum_label] += 1

    assert label_counts[FailureType.STATE_PERSISTENCE_ERROR] == 5
    assert label_counts[FailureType.REASONING_DEFICIT] == 5
    # The synthetic data does not include PASS scenarios
    assert label_counts[FailureType.PASS] == 0