import os
import json
import numpy as np
import matplotlib.pyplot as plt
import gymnasium as gym
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

# Ensure directories exist
os.makedirs("data", exist_ok=True)
os.makedirs("figures", exist_ok=True)

def create_dataset(env_name="FrozenLake-v1", num_episodes=500, seed=42):
    """
    Generates a real-world dataset of (State, Action, NextState, Reward) tuples
    from a real Gymnasium environment.
    """
    env = gym.make(env_name, render_mode=None)
    env.reset(seed=seed)
    
    states = []
    actions = []
    next_states = []
    rewards = []
    dones = []
    
    print(f"Collecting {num_episodes} episodes from {env_name}...")
    
    for _ in range(num_episodes):
        obs, info = env.reset()
        done = False
        truncated = False
        
        while not (done or truncated):
            # Random policy for data collection (standard for world model pre-training)
            action = env.action_space.sample()
            next_obs, reward, terminated, truncated, _ = env.step(action)
            
            states.append(obs)
            actions.append(action)
            next_states.append(next_obs)
            rewards.append(reward)
            dones.append(terminated or truncated)
            
            obs = next_obs
            
    env.close()
    
    return np.array(states), np.array(actions), np.array(next_states), np.array(rewards), np.array(dones)

class WorldModelLSTM(nn.Module):
    """
    A small LSTM-based World Model.
    Input: [State, Action]
    Output: Predicted Next State (classification over state space) + Predicted Reward
    """
    def __init__(self, state_dim, action_dim, num_states, hidden_dim=64):
        super().__init__()
        self.embedding = nn.Embedding(num_states, hidden_dim)
        self.action_embedding = nn.Embedding(action_dim, hidden_dim)
        self.lstm = nn.LSTM(input_size=hidden_dim * 2, hidden_size=hidden_dim, batch_first=True)
        self.state_head = nn.Linear(hidden_dim, num_states)
        self.reward_head = nn.Linear(hidden_dim, 1)
        
    def forward(self, states, actions):
        # states: (batch, seq_len), actions: (batch, seq_len)
        s_emb = self.embedding(states)
        a_emb = self.action_embedding(actions)
        x = torch.cat([s_emb, a_emb], dim=-1)
        
        lstm_out, _ = self.lstm(x)
        # Use the last output for prediction
        last_out = lstm_out[:, -1, :]
        
        pred_state = self.state_head(last_out)
        pred_reward = self.reward_head(last_out)
        
        return pred_state, pred_reward

def train_world_model(train_data, val_data, epochs=5, batch_size=32, lr=0.001):
    """
    Trains the World Model on the collected real data.
    """
    states, actions, next_states, rewards, _ = train_data
    val_states, val_actions, val_next_states, val_rewards, _ = val_data
    
    num_states = np.max(next_states) + 1
    action_dim = np.max(actions) + 1
    state_dim = 1 # FrozenLake state is an integer index
    
    model = WorldModelLSTM(state_dim, action_dim, num_states, hidden_dim=64)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion_state = nn.CrossEntropyLoss()
    criterion_reward = nn.MSELoss()
    
    # Convert to tensors
    train_ds = TensorDataset(
        torch.tensor(states, dtype=torch.long),
        torch.tensor(actions, dtype=torch.long),
        torch.tensor(next_states, dtype=torch.long),
        torch.tensor(rewards, dtype=torch.float32)
    )
    val_ds = TensorDataset(
        torch.tensor(val_states, dtype=torch.long),
        torch.tensor(val_actions, dtype=torch.long),
        torch.tensor(val_next_states, dtype=torch.long),
        torch.tensor(val_rewards, dtype=torch.float32)
    )
    
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)
    
    history = {"train_loss": [], "val_accuracy": []}
    
    print("Starting Training...")
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for b_states, b_actions, b_next_states, b_rewards in train_loader:
            optimizer.zero_grad()
            
            # We need sequences, so we simulate a sequence of length 1 for simplicity in this small scale
            # In a full world model, we'd pass longer sequences. Here we treat each transition as a 1-step sequence.
            # To make it LSTM-able, we unsqueeze to (batch, 1, feature)
            b_states = b_states.unsqueeze(1)
            b_actions = b_actions.unsqueeze(1)
            
            pred_state, pred_reward = model(b_states, b_actions)
            
            loss_state = criterion_state(pred_state, b_next_states)
            loss_reward = criterion_reward(pred_reward.squeeze(), b_rewards)
            
            loss = loss_state + loss_reward
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            
        avg_loss = total_loss / len(train_loader)
        
        # Validation
        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for b_states, b_actions, b_next_states, b_rewards in val_loader:
                b_states = b_states.unsqueeze(1)
                b_actions = b_actions.unsqueeze(1)
                pred_state, _ = model(b_states, b_actions)
                pred_next = pred_state.argmax(dim=1)
                
                correct += (pred_next == b_next_states).sum().item()
                total += b_next_states.size(0)
        
        val_acc = correct / total
        history["train_loss"].append(avg_loss)
        history["val_accuracy"].append(val_acc)
        
        print(f"Epoch {epoch+1}/{epochs} | Loss: {avg_loss:.4f} | Val Acc: {val_acc:.4f}")
        
    return model, history

def evaluate_baseline_and_model(model, test_data):
    """
    Evaluates the trained model against a naive 'Last State' baseline.
    """
    states, actions, next_states, rewards, _ = test_data
    
    # Baseline: Predict next state == current state (random walk assumption)
    baseline_correct = (states == next_states).sum()
    baseline_total = len(states)
    baseline_acc = baseline_correct / baseline_total
    
    # Model Evaluation
    model_correct = 0
    model_total = 0
    
    model.eval()
    with torch.no_grad():
        # Process in batches to avoid memory issues
        batch_size = 128
        for i in range(0, len(states), batch_size):
            b_states = torch.tensor(states[i:i+batch_size], dtype=torch.long).unsqueeze(1)
            b_actions = torch.tensor(actions[i:i+batch_size], dtype=torch.long).unsqueeze(1)
            b_next_states = torch.tensor(next_states[i:i+batch_size], dtype=torch.long)
            
            pred_state, _ = model(b_states, b_actions)
            pred_next = pred_state.argmax(dim=1)
            
            model_correct += (pred_next == b_next_states).sum().item()
            model_total += b_next_states.size(0)
            
    model_acc = model_correct / model_total
    
    return {
        "baseline_accuracy": float(baseline_acc),
        "model_accuracy": float(model_acc),
        "improvement": float(model_acc - baseline_acc)
    }

def plot_results(history, results):
    plt.figure(figsize=(10, 5))
    
    # Plot Training History
    plt.subplot(1, 2, 1)
    plt.plot(history["train_loss"], label="Train Loss", color="blue")
    plt.title("Training Loss")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.legend()
    plt.grid(True)
    
    # Plot Accuracy Comparison
    plt.subplot(1, 2, 2)
    plt.bar(["Baseline (Last State)", "World Model (LSTM)"], 
            [results["baseline_accuracy"], results["model_accuracy"]], 
            color=["gray", "green"])
    plt.title("Next-State Prediction Accuracy")
    plt.ylabel("Accuracy")
    plt.ylim(0, 1.0)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig("figures/prediction_accuracy.png", dpi=150)
    plt.close()

def main():
    print("--- Qwen-AgentWorld Adaptation: Small-Scale World Model ---")
    
    # 1. Data Collection (Real Data from Gymnasium)
    all_states, all_actions, all_next_states, all_rewards, all_dones = create_dataset(
        env_name="FrozenLake-v1", 
        num_episodes=600, 
        seed=42
    )
    
    # Split: 80% Train, 10% Val, 10% Test
    n = len(all_states)
    indices = np.arange(n)
    np.random.shuffle(indices)
    
    train_end = int(0.8 * n)
    val_end = int(0.9 * n)
    
    train_idx = indices[:train_end]
    val_idx = indices[train_end:val_end]
    test_idx = indices[val_end:]
    
    train_data = (all_states[train_idx], all_actions[train_idx], all_next_states[train_idx], all_rewards[train_idx], all_dones[train_idx])
    val_data = (all_states[val_idx], all_actions[val_idx], all_next_states[val_idx], all_rewards[val_idx], all_dones[val_idx])
    test_data = (all_states[test_idx], all_actions[test_idx], all_next_states[test_idx], all_rewards[test_idx], all_dones[test_idx])
    
    print(f"Dataset sizes: Train={len(train_data[0])}, Val={len(val_data[0])}, Test={len(test_data[0])}")
    
    # 2. Training
    model, history = train_world_model(train_data, val_data, epochs=5, batch_size=64)
    
    # 3. Evaluation
    results = evaluate_baseline_and_model(model, test_data)
    
    # 4. Save Outputs
    with open("data/model_results.json", "w") as f:
        json.dump({
            "model_type": "LSTM (Small-Scale Proxy)",
            "environment": "FrozenLake-v1 (Real)",
            "epochs": 5,
            "history": history,
            "evaluation": results
        }, f, indent=2)
        
    plot_results(history, results)
    
    print("\n--- Results Summary ---")
    print(f"Baseline Accuracy: {results['baseline_accuracy']:.4f}")
    print(f"World Model Accuracy: {results['model_accuracy']:.4f}")
    print(f"Improvement: {results['improvement']:.4f}")
    print("\nArtifacts written to:")
    print("  - data/model_results.json")
    print("  - figures/prediction_accuracy.png")

if __name__ == "__main__":
    main()
