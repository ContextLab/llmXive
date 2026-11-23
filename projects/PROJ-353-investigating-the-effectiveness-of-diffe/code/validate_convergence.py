"""
Convergence Logic Validator (T012)

Verifies that the logic for marking a run as "censored" matches the spec definition (FR-005).
FR-005 Definition: A run is censored if accuracy < 0.90 (CONVERGENCE_THRESHOLD) within max epochs (MAX_EPOCHS).
Conversely, a run is "converged" if accuracy >= 0.90 at any point within the allowed epochs.
"""
import sys
from typing import List, Dict, Any, Tuple
from utils import CONVERGENCE_THRESHOLD, MAX_EPOCHS


def determine_convergence_status(trajectory: List[Dict[str, float]]) -> Tuple[str, int, float]:
    """
    Determines the convergence status based on the trajectory.

    Args:
        trajectory: List of dicts containing 'epoch', 'loss', 'accuracy'.

    Returns:
        Tuple of (status, steps_to_convergence, final_accuracy)
        - status: "converged" or "censored"
        - steps_to_convergence: The epoch number where convergence was first achieved, or MAX_EPOCHS if censored.
        - final_accuracy: The accuracy at the last epoch.
    """
    final_accuracy = trajectory[-1]["accuracy"]
    steps_to_convergence = MAX_EPOCHS
    status = "censored"

    for step in trajectory:
        if step["accuracy"] >= CONVERGENCE_THRESHOLD:
            status = "converged"
            steps_to_convergence = step["epoch"]
            break

    return status, steps_to_convergence, final_accuracy


def validate_convergence_logic() -> bool:
    """
    Runs unit tests to assert censored status is correctly assigned for edge cases.
    Returns True if all tests pass, False otherwise.
    """
    all_passed = True

    # Test Case 1: Converged at first epoch
    traj1 = [{"epoch": 1, "loss": 0.5, "accuracy": 0.95}]
    status1, steps1, acc1 = determine_convergence_status(traj1)
    assert status1 == "converged", f"Test 1 Failed: Expected 'converged', got '{status1}'"
    assert steps1 == 1, f"Test 1 Failed: Expected steps=1, got {steps1}"
    print("✓ Test 1 Passed: Converged at first epoch.")

    # Test Case 2: Converged at last epoch (exactly MAX_EPOCHS)
    traj2 = [
        {"epoch": i, "loss": 1.0 - i * 0.001, "accuracy": 0.80 + (i * 0.01)}
        for i in range(1, MAX_EPOCHS + 1)
    ]
    # Force last accuracy to be exactly threshold
    traj2[-1]["accuracy"] = CONVERGENCE_THRESHOLD
    status2, steps2, acc2 = determine_convergence_status(traj2)
    assert status2 == "converged", f"Test 2 Failed: Expected 'converged' (threshold met), got '{status2}'"
    assert steps2 == MAX_EPOCHS, f"Test 2 Failed: Expected steps={MAX_EPOCHS}, got {steps2}"
    print(f"✓ Test 2 Passed: Converged exactly at threshold (epoch {MAX_EPOCHS}).")

    # Test Case 3: Censored (accuracy < threshold at max epoch)
    traj3 = [
        {"epoch": i, "loss": 1.0, "accuracy": 0.89}
        for i in range(1, MAX_EPOCHS + 1)
    ]
    status3, steps3, acc3 = determine_convergence_status(traj3)
    assert status3 == "censored", f"Test 3 Failed: Expected 'censored', got '{status3}'"
    assert steps3 == MAX_EPOCHS, f"Test 3 Failed: Expected steps={MAX_EPOCHS}, got {steps3}"
    print(f"✓ Test 3 Passed: Censored (accuracy {acc3} < {CONVERGENCE_THRESHOLD} at epoch {MAX_EPOCHS}).")

    # Test Case 4: Edge case - 0.899999 (just below threshold)
    traj4 = [
        {"epoch": i, "loss": 1.0, "accuracy": 0.899999}
        for i in range(1, MAX_EPOCHS + 1)
    ]
    status4, steps4, acc4 = determine_convergence_status(traj4)
    assert status4 == "censored", f"Test 4 Failed: Expected 'censored', got '{status4}'"
    print(f"✓ Test 4 Passed: Censored (accuracy 0.899999 < {CONVERGENCE_THRESHOLD}).")

    # Test Case 5: Mixed trajectory - converges early
    traj5 = [
        {"epoch": 1, "loss": 0.5, "accuracy": 0.5},
        {"epoch": 2, "loss": 0.3, "accuracy": 0.85},
        {"epoch": 3, "loss": 0.1, "accuracy": 0.91},
        {"epoch": 4, "loss": 0.05, "accuracy": 0.95},
    ]
    status5, steps5, acc5 = determine_convergence_status(traj5)
    assert status5 == "converged", f"Test 5 Failed: Expected 'converged', got '{status5}'"
    assert steps5 == 3, f"Test 5 Failed: Expected steps=3, got {steps5}"
    print(f"✓ Test 5 Passed: Converged early at epoch 3.")

    if all_passed:
        print("\n✅ All convergence logic validation tests passed.")
        print(f"   Threshold: {CONVERGENCE_THRESHOLD}")
        print(f"   Max Epochs: {MAX_EPOCHS}")
        return True
    else:
        print("\n❌ Some validation tests failed.")
        return False


def main():
    """Entry point for the validator."""
    print("Starting Convergence Logic Validation (T012)...")
    print(f"Constants loaded from utils.py: CONVERGENCE_THRESHOLD={CONVERGENCE_THRESHOLD}, MAX_EPOCHS={MAX_EPOCHS}")
    
    success = validate_convergence_logic()
    
    if not success:
        sys.exit(1)
    
    print("\nValidation complete. Logic is consistent with FR-005.")


if __name__ == "__main__":
    main()
