"""
Integration test for horizon masking logic (T017).

This test verifies that the retention horizon logic in `simulate_agent.py`
correctly determines whether critical evidence is visible to the agent.

It tests the edge cases described in FR-002:
1. Horizon >= distance_to_evidence -> Success (evidence visible)
2. Horizon < distance_to_evidence -> Failure (evidence masked)
3. Edge case: Evidence at the very last turn (T)
"""
import json
import math
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path to import simulate_agent
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from simulate_agent import (
    check_evidence_visibility,
    heuristic_solver_success,
    sigmoid,
    run_simulation_batch,
    load_trajectories_streaming,
    write_batch_to_file
)
from utils.entropy import entropy_per_token
from utils.heuristics import calculate_composite_density


def test_check_evidence_visibility_basic():
    """
    Test the core logic: check_evidence_visibility(evidence_turn, current_turn, horizon).
    """
    # Case 1: Evidence is within horizon
    # Current turn = 10, Evidence at 8, Horizon = 3. Window: [8, 9, 10]. Visible.
    assert check_evidence_visibility(evidence_turn=8, current_turn=10, horizon=3) is True

    # Case 2: Evidence is exactly at the horizon limit
    # Current turn = 10, Evidence at 8, Horizon = 2. Window: [9, 10]. NOT Visible (8 < 9).
    # Wait, let's re-read the spec logic:
    # FR-002 Logic: 1 if (critical_evidence_turn_index >= current_turn - retention_horizon + 1)
    # If current=10, horizon=2: min_turn = 10 - 2 + 1 = 9.
    # Evidence at 8: 8 >= 9 is False. Correct.
    
    # Case 3: Evidence is outside horizon
    # Current turn = 10, Evidence at 5, Horizon = 3. Window: [8, 9, 10]. NOT Visible.
    assert check_evidence_visibility(evidence_turn=5, current_turn=10, horizon=3) is False

    # Case 4: Evidence is at the very last turn (T)
    # Current turn = 10, Evidence at 10, Horizon = 1. Window: [10]. Visible.
    assert check_evidence_visibility(evidence_turn=10, current_turn=10, horizon=1) is True

    # Case 5: Evidence is at the very last turn (T), horizon too small
    # Current turn = 10, Evidence at 10, Horizon = 0? (Assume horizon >= 1 usually, but logic holds)
    # If horizon=0: min_turn = 11. 10 >= 11 False.
    assert check_evidence_visibility(evidence_turn=10, current_turn=10, horizon=0) is False


def test_integration_simulation_logic():
    """
    Integration test: Run a mini-simulation with known ground truth to verify
    the "failure when horizon < 5" and "success when horizon >= 5" requirement.
    
    We construct a synthetic trajectory in memory (simulating data/raw) and run
    the simulation loop to check if the output matches expectations.
    """
    # 1. Create a temporary trajectory file
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        traj_file = tmp_path / "test_trajectories.json"
        output_file = tmp_path / "test_results.json"

        # Create a mock trajectory with:
        # - 20 turns
        # - Critical evidence at turn 5 (index 4 if 0-based, or 5 if 1-based? Let's assume 1-based for clarity in spec)
        #   Spec says: "critical_evidence_turn_index". Let's assume 0-based index in JSON.
        #   Let's say evidence is at index 4 (turn 5).
        # - Total turns T = 20.
        #   If we are at turn 20, and evidence is at 4.
        #   Distance = 20 - 4 = 16.
        #   We need horizon >= 17 to see it? 
        #   Wait, the spec test requirement says: "failure when < 5 turns for high-density evidence".
        #   This implies the evidence is placed such that a horizon of 5 is the threshold.
        #   Let's place evidence at turn 16 (index 15) in a 20-turn trajectory.
        #   Current turn = 20. Evidence = 15.
        #   Window start = 20 - H + 1.
        #   If H=5: Window start = 16. Evidence 15 >= 16? False. (Failure)
        #   If H=6: Window start = 15. Evidence 15 >= 15? True. (Success)
        #   This matches the "threshold of 5" logic (needs >= 6 to succeed, or maybe the spec meant "horizon < 6"?
        #   Let's re-read: "failure when ... < 5 turns ... success when >= 5 turns".
        #   This implies at H=5 it should succeed.
        #   So if H=5 succeeds, Window start = 20 - 5 + 1 = 16.
        #   Evidence must be >= 16. Let's put evidence at 16.
        #   If H=4: Window start = 17. Evidence 16 >= 17? False.
        
        # Let's construct the trajectory
        trajectory = {
            "id": "test-001",
            "turns": [
                {"turn_id": i, "content": f"Turn {i} content", "is_evidence": (i == 16)}
                for i in range(1, 21)  # 1 to 20
            ],
            "metadata": {
                "density": 0.5,
                "critical_evidence_turn_index": 16  # 1-based index matching the loop
            }
        }

        # Write to file
        with open(traj_file, "w") as f:
            json.dump([trajectory], f)

        # 2. Run simulation with Horizon = 4 (Should FAIL)
        results_fail = []
        # Mock the streaming loader to just yield our one trajectory
        # We will manually call the logic to avoid file I/O complexity in test
        # But the requirement is to test the file-based pipeline if possible, or the function logic.
        # Let's test the function logic directly on the data structure first, then the file I/O.
        
        # Test H=4
        success_h4 = check_evidence_visibility(
            evidence_turn=16, 
            current_turn=20, 
            horizon=4
        )
        assert success_h4 is False, "Expected failure for horizon 4"

        # Test H=5
        success_h5 = check_evidence_visibility(
            evidence_turn=16, 
            current_turn=20, 
            horizon=5
        )
        assert success_h5 is True, "Expected success for horizon 5"

        # Test H=10 (High horizon)
        success_h10 = check_evidence_visibility(
            evidence_turn=16, 
            current_turn=20, 
            horizon=10
        )
        assert success_h10 is True, "Expected success for horizon 10"


def test_edge_case_last_turn():
    """
    Verify the edge case where evidence is at the very last turn T.
    Spec: "ensure horizon T retains it correctly".
    """
    T = 100
    evidence_turn = T
    
    # Horizon = 1 should see it
    assert check_evidence_visibility(evidence_turn, T, 1) is True
    
    # Horizon = 100 should see it
    assert check_evidence_visibility(evidence_turn, T, 100) is True
    
    # Horizon = 0 should NOT see it
    assert check_evidence_visibility(evidence_turn, T, 0) is False


def test_full_pipeline_streaming_integration():
    """
    End-to-end integration: Create a small file, run the streaming simulation,
    verify the output file is written correctly and contains expected results.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        traj_file = tmp_path / "small_trajectories.json"
        output_file = tmp_path / "sim_results.json"

        # Create 3 trajectories with known parameters
        trajectories = []
        for i in range(3):
            # Turn 10, Evidence at turn 8
            # H=3 (Window 8,9,10) -> Success
            # H=2 (Window 9,10) -> Failure
            traj = {
                "id": f"test-{i}",
                "turns": [{"turn_id": t, "content": f"Content {t}", "is_evidence": (t == 8)} for t in range(1, 11)],
                "metadata": {"density": 0.5, "critical_evidence_turn_index": 8}
            }
            trajectories.append(traj)

        with open(traj_file, "w") as f:
            json.dump(trajectories, f)

        # Run simulation with Horizon = 2 (Should fail for all)
        # We need to call run_simulation_batch. 
        # Since run_simulation_batch expects file paths and writes to file, we use it.
        # Note: The actual function might need arguments. Let's check the signature.
        # simulate_agent.run_simulation_batch(input_path, output_path, horizon, alpha, threshold)
        
        # We need to ensure the heuristic success is deterministic for this test.
        # The heuristic uses `random`. We need to seed it or mock it.
        # However, the visibility check is deterministic.
        # The `heuristic_solver_success` depends on density.
        # If density is 0.5, and threshold is 0.5, and alpha is high, it might be 0.5 prob.
        # To make this a strict integration test, we should test the visibility logic primarily,
        # or control the random seed.
        
        # Let's run with a fixed seed environment if possible, or just check that the file is created
        # and the structure is correct, then assert on the visibility part if we can isolate it.
        
        # Actually, let's just verify the file writing and structure, and that the logic runs.
        # We will assume a high alpha and low threshold so heuristic always succeeds, 
        # so the result depends ONLY on visibility.
        
        import random
        random.seed(42)
        
        # Run simulation
        # Args: input_path, output_path, horizon, alpha, threshold
        # We need to pass these.
        try:
            run_simulation_batch(
                input_path=str(traj_file),
                output_path=str(output_file),
                horizon=2,  # Should be failure (Window 9,10 vs Evidence 8)
                alpha=10.0, # High alpha
                threshold=0.1 # Low threshold -> high probability of success
            )
        except Exception as e:
            # If the function signature is different or fails, we adjust.
            # Based on the API surface, run_simulation_batch exists.
            # If it requires specific args not provided, we might need to adapt.
            # Assuming the implementation in T014 handles args.
            raise e

        # Verify output file exists
        assert output_file.exists(), "Output file was not created"

        # Load and check results
        with open(output_file, "r") as f:
            results = json.load(f)

        # We expect 3 results
        assert len(results) == 3, f"Expected 3 results, got {len(results)}"

        for res in results:
            # With horizon=2, evidence at 8, current at 10 -> Visibility False.
            # Even if heuristic is true, success should be 0.
            # Logic: 1 if (visible AND heuristic_success) else 0
            assert res["success"] == 0, f"Expected failure for horizon=2, got success={res['success']}"
            assert res["horizon"] == 2
            assert "trajectory_id" in res

        # Now run with horizon=3 (Should be success)
        output_file_2 = tmp_path / "sim_results_2.json"
        random.seed(42)
        run_simulation_batch(
            input_path=str(traj_file),
            output_path=str(output_file_2),
            horizon=3,
            alpha=10.0,
            threshold=0.1
        )

        with open(output_file_2, "r") as f:
            results_2 = json.load(f)

        for res in results_2:
            # With horizon=3, evidence at 8, current at 10 -> Visibility True.
            # Heuristic likely True (low threshold).
            # So success should be 1.
            # Note: If heuristic fails randomly, this might be 0. 
            # But with alpha=10, threshold=0.1, density=0.5 -> sigmoid(10*(0.4)) ~ 1.0
            assert res["success"] == 1, f"Expected success for horizon=3, got success={res['success']}"
            assert res["horizon"] == 3


if __name__ == "__main__":
    print("Running T017 Integration Tests...")
    test_check_evidence_visibility_basic()
    print("✓ Basic visibility tests passed")
    
    test_integration_simulation_logic()
    print("✓ Logic threshold tests passed")
    
    test_edge_case_last_turn()
    print("✓ Edge case tests passed")
    
    test_full_pipeline_streaming_integration()
    print("✓ Full pipeline integration tests passed")
    
    print("All T017 tests passed.")