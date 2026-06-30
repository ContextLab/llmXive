import os
import sys
import json
import random
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for CI
import matplotlib.pyplot as plt

# --- Configuration & Fallbacks ---
# If heavy dependencies fail, we fallback to a pure numpy/scipy implementation
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("WARNING: PyTorch not found. Running in pure NumPy fallback mode.")

# --- Synthetic Data Generator ---
def generate_synthetic_data(n_users=200, n_items=500, seq_len=10, interaction_rate=0.3, seed=42):
    """
    Generates a small, CPU-tractable synthetic dataset mimicking the structure
    of the Proactive Recommendation datasets (user sequences of item IDs).
    """
    random.seed(seed)
    np.random.seed(seed)
    
    # Create user-item interaction history
    # Format: {user_id: [item_id_1, item_id_2, ...]}
    data = {}
    
    for u in range(n_users):
        # Random sequence length between 3 and seq_len
        current_len = random.randint(3, seq_len)
        # Sample unique items
        items = random.sample(range(n_items), current_len)
        data[u] = items
    
    # Save to JSON format expected by the original dataset loader
    output_path = "data/synthetic_train.json"
    os.makedirs("data", exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f)
    
    # Create a dummy id_mapping file
    mapping = {
        "user2id": {str(u): u for u in range(n_users)},
        "item2id": {str(i): i for i in range(n_items)}
    }
    mapping_path = "data/synthetic_train.datamaps"
    with open(mapping_path, 'w') as f:
        json.dump(mapping, f)
        
    return output_path, mapping_path, n_users, n_items

# --- Simplified ProRL Logic (CPU-Only) ---
# The core of the paper is:
# 1. Path-level rewards are decomposed into step-level rewards.
# 2. "Stepwise Reward Centering" subtracts the mean to remove length bias.
# 3. "Position-Specific Advantage" reduces variance.
# We will simulate this process on small synthetic paths.

class SimpleProRLSimulator:
    def __init__(self, n_items, device="cpu"):
        self.n_items = n_items
        self.device = device
        self.gamma = 0.95  # Discount factor
        
        # Initialize a tiny policy network (just a linear layer for demonstration)
        # Input: current item embedding (one-hot or simple ID), Output: probs over next items
        if TORCH_AVAILABLE:
            self.policy_net = nn.Linear(n_items, n_items).to(device)
            # Initialize weights small
            nn.init.xavier_uniform_(self.policy_net.weight)
            self.policy_net.bias.data.zero_()
        else:
            # Fallback: Random matrix
            self.policy_weights = np.random.randn(n_items, n_items) * 0.01
            
    def get_action_probs(self, current_item_id):
        if TORCH_AVAILABLE:
            with torch.no_grad():
                x = torch.zeros(self.n_items, device=self.device)
                x[current_item_id] = 1.0
                logits = self.policy_net(x)
                probs = F.softmax(logits, dim=0)
                return probs.cpu().numpy()
        else:
            # Fallback: Softmax of random logits
            logits = self.policy_weights[current_item_id]
            exp_logits = np.exp(logits - np.max(logits))
            return exp_logits / np.sum(exp_logits)

    def sample_path(self, start_item, max_len=5):
        """Simulate a user path of recommendations."""
        path = [start_item]
        probs_history = []
        
        current = start_item
        for _ in range(max_len - 1):
            probs = self.get_action_probs(current)
            probs_history.append(probs)
            
            # Sample next item
            next_item = np.random.choice(self.n_items, p=probs)
            path.append(next_item)
            current = next_item
            
            # Stop if we hit a "sink" or random chance (simulating user drop-off)
            if np.random.random() < 0.1: 
                break
                
        return path, probs_history

    def compute_step_rewards(self, path):
        """
        Simulate the reward function.
        Paper: Rewards are decomposed. 
        We simulate a positive reward for reaching a "target" item, 
        and a small negative reward for length (to simulate cost).
        """
        rewards = []
        for i in range(len(path) - 1):
            # Simulated reward: 1.0 if we move towards a "target" (last item), else 0.1
            # Plus a small step penalty
            r = 0.1 
            if i == len(path) - 2:
                r += 1.0 # Terminal reward
            rewards.append(r)
        return rewards

    def stepwise_reward_centering(self, rewards):
        """
        Core Mechanism 1: Subtract expected reward (mean) to neutralize length bias.
        """
        mean_reward = np.mean(rewards)
        centered_rewards = [r - mean_reward for r in rewards]
        return centered_rewards

    def position_specific_advantage(self, centered_rewards, gamma=0.95):
        """
        Core Mechanism 2: Compute advantage using discounted returns.
        A_t = R_t + gamma * R_{t+1} ... - V(s_t)
        Here we simplify: Advantage = Centered Return - Mean(Centered Return)
        """
        # Calculate discounted return for each step
        returns = []
        for t in range(len(centered_rewards)):
            G_t = 0
            for k, r in enumerate(centered_rewards[t:]):
                G_t += (gamma ** k) * r
            returns.append(G_t)
        
        # Baseline: mean of returns
        baseline = np.mean(returns)
        advantages = [r - baseline for r in returns]
        
        return advantages

    def update_policy(self, path, advantages):
        """
        Simulate a policy gradient update step.
        """
        if TORCH_AVAILABLE:
            # In a real run, we would compute gradients here.
            # For this adaptation, we just simulate the effect:
            # If advantage > 0, we slightly increase prob of the chosen action.
            with torch.no_grad():
                for i, (current_item, next_item) in enumerate(zip(path[:-1], path[1:])):
                    if i < len(advantages):
                        adv = advantages[i]
                        # Simple heuristic update: push towards next_item if adv > 0
                        if adv > 0:
                            self.policy_net.weight.data[next_item, current_item] += 0.01 * adv
                        else:
                            self.policy_net.weight.data[next_item, current_item] -= 0.01 * abs(adv)
        else:
            # Numpy fallback
            for i, (current_item, next_item) in enumerate(zip(path[:-1], path[1:])):
                if i < len(advantages):
                    adv = advantages[i]
                    if adv > 0:
                        self.policy_weights[next_item, current_item] += 0.01 * adv
                    else:
                        self.policy_weights[next_item, current_item] -= 0.01 * abs(adv)

def run_experiment():
    print("Starting ProRL Adaptation Experiment (CPU-Only)...")
    
    # 1. Setup Data
    print("Generating synthetic dataset...")
    train_path, map_path, n_users, n_items = generate_synthetic_data()
    
    # 2. Initialize Simulator
    device = "cpu"
    simulator = SimpleProRLSimulator(n_items, device)
    
    # 3. Run Training Loop (Tiny scale)
    epochs = 5
    batch_size = 4
    results = {
        "epoch": [],
        "avg_reward": [],
        "avg_advantage_variance": [],
        "path_length": []
    }
    
    # Load synthetic data
    with open(train_path, 'r') as f:
        raw_data = json.load(f)
    # Convert to list of sequences
    sequences = [v for v in raw_data.values()]
    
    print(f"Running {epochs} epochs on {len(sequences)} synthetic user sequences...")
    
    for epoch in range(epochs):
        epoch_rewards = []
        epoch_adv_variances = []
        epoch_lengths = []
        
        # Mini-batch processing
        for i in range(0, len(sequences), batch_size):
            batch_seqs = sequences[i:i+batch_size]
            
            for seq in batch_seqs:
                if len(seq) < 2: continue
                
                # Simulate a proactive path starting from the first item
                start_item = seq[0]
                # In real paper, we generate a path of recommendations.
                # Here we simulate a short path of length 3-5
                path, probs = simulator.sample_path(start_item, max_len=4)
                
                # Compute rewards
                raw_rewards = simulator.compute_step_rewards(path)
                
                # Mechanism 1: Centering
                centered_rewards = simulator.stepwise_reward_centering(raw_rewards)
                
                # Mechanism 2: Advantage
                advantages = simulator.position_specific_advantage(centered_rewards)
                
                # Update Policy
                simulator.update_policy(path, advantages)
                
                # Metrics
                epoch_rewards.append(np.mean(raw_rewards))
                epoch_adv_variances.append(np.var(advantages))
                epoch_lengths.append(len(path))
        
        # Aggregate metrics
        avg_reward = np.mean(epoch_rewards)
        avg_adv_var = np.mean(epoch_adv_variances)
        avg_len = np.mean(epoch_lengths)
        
        results["epoch"].append(epoch + 1)
        results["avg_reward"].append(avg_reward)
        results["avg_advantage_variance"].append(avg_adv_var)
        results["path_length"].append(avg_len)
        
        print(f"Epoch {epoch+1}: Avg Reward={avg_reward:.4f}, Adv Var={avg_adv_var:.4f}, Len={avg_len:.2f}")

    # 4. Save Outputs
    os.makedirs("data", exist_ok=True)
    os.makedirs("figures", exist_ok=True)
    
    # Save CSV
    df = pd.DataFrame(results)
    csv_path = "data/prorl_results.csv"
    df.to_csv(csv_path, index=False)
    print(f"Results saved to {csv_path}")
    
    # Save JSON summary
    summary = {
        "method": "ProRL_Adaptation",
        "scale": "Synthetic (200 users, 500 items)",
        "approximation": "Tiny policy network, 5 epochs, 4-step paths",
        "final_reward": float(avg_reward),
        "final_adv_variance": float(avg_adv_var)
    }
    json_path = "data/prorl_summary.json"
    with open(json_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"Summary saved to {json_path}")
    
    # Plot Results
    plt.figure(figsize=(10, 6))
    plt.subplot(1, 2, 1)
    plt.plot(results["epoch"], results["avg_reward"], marker='o')
    plt.title("Average Path Reward (ProRL Centering)")
    plt.xlabel("Epoch")
    plt.ylabel("Reward")
    plt.grid(True)
    
    plt.subplot(1, 2, 2)
    plt.plot(results["epoch"], results["avg_advantage_variance"], marker='s', color='orange')
    plt.title("Advantage Variance (Position-Specific)")
    plt.xlabel("Epoch")
    plt.ylabel("Variance")
    plt.grid(True)
    
    plt.tight_layout()
    fig_path = "figures/prorl_training_curve.png"
    plt.savefig(fig_path)
    plt.close()
    print(f"Figure saved to {fig_path}")
    
    print("Experiment completed successfully.")
    return True

if __name__ == "__main__":
    try:
        run_experiment()
    except Exception as e:
        print(f"Error during execution: {e}")
        # Ensure we still write a failure artifact so the pipeline doesn't crash
        os.makedirs("data", exist_ok=True)
        with open("data/prorl_summary.json", 'w') as f:
            json.dump({"status": "failed", "error": str(e)}, f)
        raise
