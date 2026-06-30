import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import json

# Ensure output directories exist
os.makedirs("data", exist_ok=True)
os.makedirs("figures", exist_ok=True)

def generate_synthetic_gradients(n_samples=5000, n_dims=1000, n_shared=8000, n_discrim=2000):
    """
    Generates synthetic token-gradient vectors mimicking the RLVR scenario described in the paper.
    
    - Shared patterns: High frequency, similar directions, dilute the signal.
    - Discriminative patterns: Sparse, unique directions, carry the reward signal.
    """
    np.random.seed(42)
    
    # 1. Shared Pattern Vector (The "Noise" / Formatting tokens)
    # This vector represents the common direction (e.g., "Answer:", newlines)
    shared_direction = np.random.randn(n_dims)
    shared_direction = shared_direction / np.linalg.norm(shared_direction)
    
    # Generate samples with strong shared component
    shared_vectors = np.outer(np.random.randn(n_samples), shared_direction) * 0.8
    
    # 2. Discriminative Signal (The "Signal" / Reasoning tokens)
    # Create a few specific directions that differ between positive and negative rewards
    # We'll create 20 distinct "reasoning" directions
    n_reasoning_dirs = 20
    reasoning_dirs = np.random.randn(n_reasoning_dirs, n_dims)
    reasoning_dirs = reasoning_dirs / np.linalg.norm(reasoning_dirs, axis=1, keepdims=True)
    
    # Assign each sample to a reasoning direction randomly
    sample_reasoning_idx = np.random.randint(0, n_reasoning_dirs, size=n_samples)
    reasoning_vectors = np.array([reasoning_dirs[i] for i in sample_reasoning_idx]) * 0.2
    
    # Combine to form raw gradients
    raw_gradients = shared_vectors + reasoning_vectors
    
    # 3. Assign Rewards (Advantages)
    # Positive reward (+1) if the reasoning direction aligns with a specific "correct" set
    # Negative reward (-1) if it aligns with a "wrong" set
    # We define the first half of reasoning directions as "correct", second half as "wrong"
    correct_dirs = set(range(n_reasoning_dirs // 2))
    
    advantages = np.zeros(n_samples)
    for i in range(n_samples):
        if sample_reasoning_idx[i] in correct_dirs:
            advantages[i] = 1.0 + np.random.randn() * 0.1 # High reward
        else:
            advantages[i] = -1.0 + np.random.randn() * 0.1 # Low reward
            
    return raw_gradients, advantages, reasoning_dirs

def compute_standard_centroids(gradients, advantages):
    """
    Standard RLVR: Centroid = sum(advantage * gradient) / sum(|advantage|)
    This is dominated by the shared patterns because they are present in ALL samples.
    """
    # Weighted average
    weighted_sum = np.sum(advantages[:, np.newaxis] * gradients, axis=0)
    total_weight = np.sum(np.abs(advantages))
    
    if total_weight == 0:
        return np.zeros_like(gradients[0]), np.zeros_like(gradients[0])
        
    centroid = weighted_sum / total_weight
    return centroid

def compute_delta_centroids(gradients, advantages):
    """
    DelTA Proxy:
    1. Estimate discriminative power of each token (dimension) by checking correlation with advantage.
    2. Reweight gradients based on this power.
    3. Compute new centroid.
    """
    # 1. Calculate discriminative coefficient (correlation) for each dimension
    # Correlation between gradient values and advantages across samples
    # Using Pearson correlation logic simplified: cov(x, y) / (std(x)*std(y))
    # Or simpler: dot product of centered gradient with centered advantages
    
    # Center the data
    mean_grad = np.mean(gradients, axis=0)
    centered_grads = gradients - mean_grad
    mean_adv = np.mean(advantages)
    centered_adv = advantages - mean_adv
    
    # Discriminative score per dimension: sum( (grad - mean) * (adv - mean) )
    # This highlights dimensions that change consistently with the reward
    discriminative_scores = np.dot(centered_grads.T, centered_adv)
    
    # Normalize scores to be positive weights (absolute value + smoothing)
    # We want to amplify dimensions that are discriminative (high abs score)
    # and suppress those that are not (low abs score, likely shared patterns)
    weights = np.abs(discriminative_scores) + 1e-6
    
    # 2. Apply weights to the gradients BEFORE averaging
    # We reweight each sample's gradient contribution by the discriminative power of its active dimensions?
    # Actually, the paper suggests reweighting the token-gradient vectors themselves.
    # Let's implement a simplified version: Scale the gradient vector of each sample by the 
    # average discriminative score of its "active" reasoning components.
    # For simplicity in this proxy: We scale the entire gradient vector of a sample 
    # by the discriminative score of the specific reasoning direction it belongs to.
    
    # Re-calculate reasoning directions for this sample (simplified logic from generation)
    # We don't have the index map here, so we approximate: 
    # We will apply the dimension-wise weights directly to the gradients.
    # This effectively suppresses dimensions that are uncorrelated with reward (shared patterns)
    # and amplifies those that are correlated.
    
    weighted_gradients = gradients * weights[np.newaxis, :]
    
    # 3. Compute centroid on weighted gradients
    weighted_sum = np.sum(advantages[:, np.newaxis] * weighted_gradients, axis=0)
    total_weight = np.sum(np.abs(advantages))
    
    if total_weight == 0:
        return np.zeros_like(gradients[0])
        
    centroid = weighted_sum / total_weight
    return centroid

def calculate_separation_metric(centroid_pos, centroid_neg):
    """
    Calculates the cosine similarity between the two centroids.
    In RLVR, we want the update directions to be distinct. 
    However, the paper argues DelTA makes the *directions* more contrastive.
    Here we measure the angle between the positive update vector and negative update vector.
    Ideally, they should be as opposite as possible (cosine ~ -1) or distinct.
    But the paper's metric is about the "discriminative power" of the direction.
    
    Let's measure the magnitude of the difference vector relative to the sum (contrast).
    Or simpler: Cosine similarity between the positive centroid and the negative centroid.
    Standard RLVR: Shared patterns dominate -> both centroids point in similar "shared" direction -> high cosine sim (bad).
    DelTA: Shared patterns suppressed -> centroids point in reasoning directions -> low/negative cosine sim (good).
    """
    norm_pos = np.linalg.norm(centroid_pos)
    norm_neg = np.linalg.norm(centroid_neg)
    
    if norm_pos == 0 or norm_neg == 0:
        return 0.0
        
    cosine_sim = np.dot(centroid_pos, centroid_neg) / (norm_pos * norm_neg)
    return cosine_sim

def main():
    print("Starting DelTA CPU Proxy Simulation...")
    
    # Generate Data
    gradients, advantages, reasoning_dirs = generate_synthetic_gradients()
    print(f"Generated {len(gradients)} synthetic token gradients.")
    
    # 1. Standard RLVR
    centroid_std = compute_standard_centroids(gradients, advantages)
    
    # 2. DelTA Proxy
    centroid_delta = compute_delta_centroids(gradients, advantages)
    
    # Calculate Separation Metrics
    # We need to split advantages to get positive and negative centroids separately?
    # The function above computes the *net* update direction (sum of pos + neg).
    # Let's compute the centroids of the POSITIVE samples and NEGATIVE samples separately.
    
    pos_mask = advantages > 0
    neg_mask = advantages < 0
    
    # Standard
    if np.sum(pos_mask) > 0:
        centroid_std_pos = np.mean(gradients[pos_mask], axis=0) # Simple mean for separation check
        centroid_std_neg = np.mean(gradients[neg_mask], axis=0)
    else:
        centroid_std_pos = np.zeros_like(gradients[0])
        centroid_std_neg = np.zeros_like(gradients[0])

    # DelTA
    if np.sum(pos_mask) > 0:
        # Re-use the weighting logic but applied to subsets?
        # For the proxy, we'll just apply the same global weights to the subsets
        weights = np.abs(np.dot((gradients - np.mean(gradients, axis=0)).T, (advantages - np.mean(advantages)))) + 1e-6
        weighted_grads = gradients * weights[np.newaxis, :]
        
        centroid_delta_pos = np.mean(weighted_grads[pos_mask], axis=0)
        centroid_delta_neg = np.mean(weighted_grads[neg_mask], axis=0)
    else:
        centroid_delta_pos = np.zeros_like(gradients[0])
        centroid_delta_neg = np.zeros_like(gradients[0])
        
    # Metrics
    sim_std = calculate_separation_metric(centroid_std_pos, centroid_std_neg)
    sim_delta = calculate_separation_metric(centroid_delta_pos, centroid_delta_neg)
    
    # The goal: DelTA should make the positive and negative centroids MORE distinct (more negative cosine sim)
    # or at least align with the true reasoning directions.
    # In our synthetic setup, shared patterns pull them together. DelTA pushes them apart.
    
    print(f"Standard RLVR Centroid Separation (Cosine Sim): {sim_std:.4f}")
    print(f"DelTA Proxy Centroid Separation (Cosine Sim): {sim_delta:.4f}")
    
    # Prepare Output Data
    results = [
        {"method": "Standard_RLVR", "cosine_similarity": sim_std, "description": "Baseline centroid separation"},
        {"method": "DelTA_Proxy", "cosine_similarity": sim_delta, "description": "Discriminative token credit assignment"}
    ]
    
    df = pd.DataFrame(results)
    df.to_csv("data/centroids_comparison.csv", index=False)
    print("Saved results to data/centroids_comparison.csv")
    
    # Visualization
    # Project to 2D using PCA or just the first two reasoning directions for visualization
    # Since we generated data with specific reasoning directions, let's project onto the first 2 reasoning directions
    proj_vectors = reasoning_dirs[:2].T # Shape (n_dims, 2)
    
    proj_std_pos = centroid_std_pos @ proj_vectors
    proj_std_neg = centroid_std_neg @ proj_vectors
    proj_delta_pos = centroid_delta_pos @ proj_vectors
    proj_delta_neg = centroid_delta_neg @ proj_vectors
    
    plt.figure(figsize=(10, 8))
    
    # Plot Standard
    plt.scatter([proj_std_pos[0]], [proj_std_pos[1]], c='red', s=100, marker='x', label='Std Positive')
    plt.scatter([proj_std_neg[0]], [proj_std_neg[1]], c='blue', s=100, marker='x', label='Std Negative')
    
    # Plot DelTA
    plt.scatter([proj_delta_pos[0]], [proj_delta_pos[1]], c='orange', s=150, marker='o', facecolors='none', edgecolors='orange', linewidth=2, label='DelTA Positive')
    plt.scatter([proj_delta_neg[0]], [proj_delta_neg[1]], c='purple', s=150, marker='o', facecolors='none', edgecolors='purple', linewidth=2, label='DelTA Negative')
    
    plt.title("Centroid Separation: Standard RLVR vs DelTA (2D Projection of Reasoning Directions)")
    plt.xlabel("Reasoning Direction 1")
    plt.ylabel("Reasoning Direction 2")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.savefig("figures/separation_analysis.png", dpi=150, bbox_inches='tight')
    print("Saved plot to figures/separation_analysis.png")
    
    print("Simulation complete.")

if __name__ == "__main__":
    main()
