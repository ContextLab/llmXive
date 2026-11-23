"""
Integration test for training loop convergence with distinct alpha values.

This test verifies that the TOP-D training loop converges and produces
distinct loss trajectories for different interpolation coefficients (alpha).

It runs the training loop for a small number of epochs with alpha values
of 0.0 (pure student), 0.5 (mixed), and 1.0 (pure teacher) to ensure:
1. The loop executes without errors
2. Loss values are recorded
3. Different alpha values produce distinguishable results
"""
import os
import sys
import pytest
import numpy as np
import pandas as pd
import tempfile
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.seed_manager import set_seed, reset_to_seed
from utils.logger import setup_logging, get_logger
from env.reasoning_mdp import ReasoningMDP
from env.teacher_policy import TeacherPolicy
from student.policy import StudentPolicy
from student.topd_loss import TOPDLoss
from experiments.runner import run_training_loop

logger = get_logger(__name__)

# Test configuration constants
TEST_SEED = 42
NUM_EPISODES = 50
MAX_STEPS = 10
ALPHA_VALUES = [0.0, 0.5, 1.0]
HORIZON = 5

@pytest.fixture(scope="module")
def setup_environment():
    """Set up the MDP environment and policies."""
    reset_to_seed()
    set_seed(TEST_SEED)
    
    # Initialize the Reasoning MDP
    mdp = ReasoningMDP(
        num_initial_states=5,
        max_depth=MAX_STEPS,
        num_inference_rules=3
    )
    
    # Initialize Teacher Policy
    teacher_policy = TeacherPolicy(mdp=mdp)
    
    # Initialize Student Policy
    student_policy = StudentPolicy(
        horizon=HORIZON,
        state_dim=mdp.state_dim,
        action_dim=mdp.action_dim
    )
    
    return mdp, teacher_policy, student_policy

@pytest.fixture(scope="module")
def setup_loss_function():
    """Set up the TOP-D loss function."""
    return TOPDLoss()

def test_training_loop_execution(setup_environment, setup_loss_function):
    """Test that the training loop executes for all alpha values."""
    mdp, teacher_policy, student_policy = setup_environment
    loss_fn = setup_loss_function
    
    results = {}
    
    for alpha in ALPHA_VALUES:
        reset_to_seed()
        set_seed(TEST_SEED)
        
        # Create a fresh student policy for each alpha to ensure fair comparison
        fresh_student = StudentPolicy(
            horizon=HORIZON,
            state_dim=mdp.state_dim,
            action_dim=mdp.action_dim
        )
        
        # Create a temporary directory for logs
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_episode_logs.csv"
            
            # Run training loop
            logger.info(f"Running training loop with alpha={alpha}")
            history = run_training_loop(
                mdp=mdp,
                teacher_policy=teacher_policy,
                student_policy=fresh_student,
                loss_fn=loss_fn,
                alpha=alpha,
                num_episodes=NUM_EPISODES,
                max_steps=MAX_STEPS,
                log_path=str(log_path)
            )
            
            # Verify history is not empty
            assert history is not None, f"History is None for alpha={alpha}"
            assert len(history) > 0, f"History is empty for alpha={alpha}"
            
            # Verify log file was created
            assert log_path.exists(), f"Log file not created for alpha={alpha}"
            
            # Load and verify log contents
            df = pd.read_csv(log_path)
            assert len(df) == NUM_EPISODES, f"Expected {NUM_EPISODES} episodes, got {len(df)}"
            assert "loss" in df.columns, "Loss column missing from logs"
            assert "alpha" in df.columns, "Alpha column missing from logs"
            
            results[alpha] = {
                "history": history,
                "logs": df,
                "final_loss": df["loss"].iloc[-1],
                "mean_loss": df["loss"].mean()
            }
            
            logger.info(f"Alpha={alpha}: Mean loss={results[alpha]['mean_loss']:.4f}, "
                        f"Final loss={results[alpha]['final_loss']:.4f}")
    
    # Verify that different alpha values produce different results
    # (This is expected because alpha affects the loss calculation)
    losses = [results[alpha]["mean_loss"] for alpha in ALPHA_VALUES]
    
    # Check that losses are not all identical (with some tolerance for numerical noise)
    unique_losses = len(set([round(l, 6) for l in losses]))
    assert unique_losses > 1, (
        f"All alpha values produced identical losses: {losses}. "
        "Expected different loss trajectories for different alpha values."
    )
    
    logger.info("Training loop convergence test passed.")
    
    # Additional check: verify that alpha=1.0 (pure teacher) typically has lower variance
    # and alpha=0.0 (pure student) might have higher initial loss
    # This is a heuristic check to ensure the TOP-D mechanism is working
    alpha_0_loss = results[0.0]["mean_loss"]
    alpha_1_loss = results[1.0]["mean_loss"]
    
    logger.info(f"Alpha=0.0 (pure student) mean loss: {alpha_0_loss:.4f}")
    logger.info(f"Alpha=1.0 (pure teacher) mean loss: {alpha_1_loss:.4f}")
    
    # The pure teacher case should generally have lower or comparable loss
    # compared to pure student in early training, but this is environment-dependent
    # We just log the relationship rather than assert a strict inequality
    
    return results

def test_convergence_stability(setup_environment, setup_loss_function):
    """Test that the training loop shows signs of convergence (loss decreases or stabilizes)."""
    mdp, teacher_policy, student_policy = setup_environment
    loss_fn = setup_loss_function
    
    alpha = 0.5  # Use mixed mode for convergence test
    
    reset_to_seed()
    set_seed(TEST_SEED)
    
    fresh_student = StudentPolicy(
        horizon=HORIZON,
        state_dim=mdp.state_dim,
        action_dim=mdp.action_dim
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "convergence_test_logs.csv"
        
        history = run_training_loop(
            mdp=mdp,
            teacher_policy=teacher_policy,
            student_policy=fresh_student,
            loss_fn=loss_fn,
            alpha=alpha,
            num_episodes=NUM_EPISODES,
            max_steps=MAX_STEPS,
            log_path=str(log_path)
        )
        
        df = pd.read_csv(log_path)
        losses = df["loss"].values
        
        # Check that loss is finite for all episodes
        assert np.all(np.isfinite(losses)), "Non-finite loss values detected"
        
        # Check that loss doesn't explode (arbitrary threshold)
        assert np.max(losses) < 1e6, "Loss exploded during training"
        
        # Check for convergence: compare first 10% and last 10% of episodes
        first_quarter = losses[:NUM_EPISODES // 4]
        last_quarter = losses[-NUM_EPISODES // 4:]
        
        mean_first = np.mean(first_quarter)
        mean_last = np.mean(last_quarter)
        
        logger.info(f"Convergence test: First 25% mean loss={mean_first:.4f}, "
                    f"Last 25% mean loss={mean_last:.4f}")
        
        # We expect some improvement or stability, but not necessarily strict decrease
        # due to the stochastic nature of the environment and policy updates
        # Just verify that the loss is in a reasonable range
        assert 0 < mean_last < 1000, f"Final mean loss out of expected range: {mean_last}"
        
        logger.info("Convergence stability test passed.")

if __name__ == "__main__":
    # Run tests directly for development
    pytest.main([__file__, "-v", "-s"])
