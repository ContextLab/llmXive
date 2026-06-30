import os
import json
import random
import math
import numpy as np
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from typing import List, Dict, Tuple, Any

# Ensure CPU-only
os.environ["CUDA_VISIBLE_DEVICES"] = ""

# --- Configuration ---
CONFIG = {
    "num_domains": 3,
    "scenes_per_domain": 50,
    "patch_size": 16,
    "model_dim": 64,
    "num_heads": 2,
    "num_layers": 2,
    "batch_size": 16,
    "num_epochs": 5,  # Tiny training for demonstration
    "domains": ["indoor", "outdoor", "egocentric"],
    "seed": 42
}

# --- Synthetic Data Generation ---
class SyntheticSpatialDataset(Dataset):
    """
    Generates synthetic 2D patches with pseudo-depth labels.
    Simulates different domain characteristics:
    - indoor: Low noise, structured geometry
    - outdoor: High noise, complex textures
    - egocentric: Motion blur (simulated by smoothing)
    """
    def __init__(self, num_samples: int, domain: str, seed: int):
        self.num_samples = num_samples
        self.domain = domain
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)
        
        self.data = []
        self.labels = []
        
        # Generate synthetic data
        for i in range(num_samples):
            # Create a random 32x32 "image" patch (downscaled for speed)
            img = np.random.rand(32, 32, 3).astype(np.float32)
            
            # Generate pseudo-depth (0-1)
            depth = np.random.rand(32, 32).astype(np.float32)
            
            # Apply domain-specific noise
            if domain == "indoor":
                noise = np.random.normal(0, 0.05, img.shape).astype(np.float32)
                depth += np.random.normal(0, 0.02, depth.shape).astype(np.float32)
            elif domain == "outdoor":
                noise = np.random.normal(0, 0.15, img.shape).astype(np.float32)
                depth += np.random.normal(0, 0.08, depth.shape).astype(np.float32)
                # Add texture-like patterns
                x = np.linspace(0, 1, 32)
                y = np.linspace(0, 1, 32)
                X, Y = np.meshgrid(x, y)
                texture = 0.1 * np.sin(10 * X) * np.cos(10 * Y)
                img += texture[..., None]
            elif domain == "egocentric":
                # Simulate motion blur by smoothing
                from scipy.ndimage import gaussian_filter
                img = gaussian_filter(img, sigma=1.0)
                depth = gaussian_filter(depth, sigma=1.0)
                noise = np.random.normal(0, 0.1, img.shape).astype(np.float32)
            
            img = np.clip(img + noise, 0, 1)
            depth = np.clip(depth, 0, 1)
            
            self.data.append(img)
            self.labels.append(depth)
        
        self.data = np.array(self.data)
        self.labels = np.array(self.labels)

    def __len__(self):
        return self.num_samples

    def __getitem__(self, idx):
        return self.data[idx], self.labels[idx]

def create_dataset(domain: str, num_samples: int, seed: int) -> SyntheticSpatialDataset:
    return SyntheticSpatialDataset(num_samples, domain, seed)

# --- Model Definitions ---

class FullContextModel(nn.Module):
    """
    Small ViT-like model with full attention (simulates 'Full-Context' paradigm).
    """
    def __init__(self, patch_size=16, dim=64, num_heads=2, num_layers=2):
        super().__init__()
        self.patch_size = patch_size
        self.dim = dim
        
        # Simple patch embedding
        self.patch_embed = nn.Conv2d(3, dim, kernel_size=patch_size, stride=patch_size)
        self.pos_embed = nn.Parameter(torch.zeros(1, 4, 4, dim))  # 32x32 -> 2x2 patches
        
        # Transformer layers
        encoder_layer = nn.TransformerEncoderLayer(d_model=dim, nhead=num_heads, batch_first=True)
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # Depth head
        self.head = nn.Sequential(
            nn.Linear(dim, dim),
            nn.ReLU(),
            nn.Linear(dim, 1)
        )
        
        self.cls_token = nn.Parameter(torch.zeros(1, 1, dim))

    def forward(self, x):
        b, c, h, w = x.shape
        # Patch embedding
        patches = self.patch_embed(x)  # [b, dim, h', w']
        patches = patches.flatten(2).transpose(1, 2)  # [b, n_patches, dim]
        
        # Add position embedding
        patches = patches + self.pos_embed[:, :patches.shape[1], :]
        
        # Add CLS token
        cls_tokens = self.cls_token.expand(b, -1, -1)
        x = torch.cat([cls_tokens, patches], dim=1)  # [b, 1+n_patches, dim]
        
        # Transformer
        x = self.transformer(x)
        
        # Use CLS token for prediction
        cls_out = x[:, 0]
        depth_pred = self.head(cls_out)
        
        # Reshape to original spatial size (simplified)
        depth_pred = depth_pred.view(b, 1, 1, 1)
        # Upsample to 32x32 (simplified)
        depth_pred = nn.functional.interpolate(depth_pred, size=(32, 32), mode='bilinear', align_corners=False)
        
        return depth_pred.squeeze(1)

class BoundedMemoryModel(nn.Module):
    """
    Model with sliding window attention (simulates 'Bounded-Memory' paradigm).
    Simplified for CPU: just uses local windows.
    """
    def __init__(self, patch_size=16, dim=64, num_heads=2, num_layers=2, window_size=2):
        super().__init__()
        self.patch_size = patch_size
        self.dim = dim
        self.window_size = window_size
        
        self.patch_embed = nn.Conv2d(3, dim, kernel_size=patch_size, stride=patch_size)
        
        # Local window attention
        encoder_layer = nn.TransformerEncoderLayer(d_model=dim, nhead=num_heads, batch_first=True, 
                                                   norm_first=True, 
                                                   # Simplified: no explicit window masking, but smaller effective context
                                                   )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        self.head = nn.Sequential(
            nn.Linear(dim, dim),
            nn.ReLU(),
            nn.Linear(dim, 1)
        )
        
        self.cls_token = nn.Parameter(torch.zeros(1, 1, dim))

    def forward(self, x):
        b, c, h, w = x.shape
        patches = self.patch_embed(x)
        patches = patches.flatten(2).transpose(1, 2)
        
        # Simulate bounded memory by truncating sequence length (simplified)
        max_len = patches.shape[1] // 2  # Use only half the context
        patches = patches[:, :max_len, :]
        
        cls_tokens = self.cls_token.expand(b, -1, -1)
        x = torch.cat([cls_tokens, patches], dim=1)
        
        x = self.transformer(x)
        cls_out = x[:, 0]
        depth_pred = self.head(cls_out)
        
        depth_pred = depth_pred.view(b, 1, 1, 1)
        depth_pred = nn.functional.interpolate(depth_pred, size=(32, 32), mode='bilinear', align_corners=False)
        
        return depth_pred.squeeze(1)

# --- Training & Evaluation ---

def train_model(model: nn.Module, train_loader: DataLoader, val_loader: DataLoader, epochs: int, device: str = "cpu"):
    model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.MSELoss()
    
    best_val_loss = float('inf')
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            
            optimizer.zero_grad()
            pred = model(batch_x)
            loss = criterion(pred, batch_y)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
        
        train_loss /= len(train_loader)
        
        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                batch_x, batch_y = batch_x.to(device), batch_y.to(device)
                pred = model(batch_x)
                loss = criterion(pred, batch_y)
                val_loss += loss.item()
        
        val_loss /= len(val_loader)
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
    
    return best_val_loss

def evaluate_model(model: nn.Module, test_loader: DataLoader, device: str = "cpu") -> float:
    model.eval()
    model.to(device)
    criterion = nn.MSELoss()
    total_loss = 0.0
    count = 0
    
    with torch.no_grad():
        for batch_x, batch_y in test_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            pred = model(batch_x)
            loss = criterion(pred, batch_y)
            total_loss += loss.item() * batch_x.size(0)
            count += batch_x.size(0)
    
    return total_loss / count

def compute_mae(model: nn.Module, test_loader: DataLoader, device: str = "cpu") -> float:
    model.eval()
    model.to(device)
    total_error = 0.0
    count = 0
    
    with torch.no_grad():
        for batch_x, batch_y in test_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            pred = model(batch_x)
            error = torch.abs(pred - batch_y).mean()
            total_error += error.item() * batch_x.size(0)
            count += batch_x.size(0)
    
    return total_error / count

# --- Main Execution ---

def main():
    print("Starting SpatialBench CPU Adaptation...")
    device = "cpu"
    
    # Create output directories
    os.makedirs("data", exist_ok=True)
    os.makedirs("figures", exist_ok=True)
    
    # Generate datasets
    datasets = {}
    for domain in CONFIG["domains"]:
        print(f"Generating synthetic data for domain: {domain}")
        train_ds = create_dataset(domain, 100, CONFIG["seed"])
        val_ds = create_dataset(domain, 30, CONFIG["seed"] + 1)
        test_ds = create_dataset(domain, 30, CONFIG["seed"] + 2)
        
        datasets[domain] = {
            "train": train_ds,
            "val": val_ds,
            "test": test_ds
        }
    
    # Save a sample of the synthetic dataset
    sample_data = {
        "domains": CONFIG["domains"],
        "samples_per_domain": 100,
        "description": "Synthetic spatial data with domain-specific noise patterns"
    }
    with open("data/synthetic_dataset.json", "w") as f:
        json.dump(sample_data, f, indent=2)
    print("Saved synthetic dataset metadata to data/synthetic_dataset.json")
    
    # Initialize models
    full_model = FullContextModel(patch_size=CONFIG["patch_size"], 
                                   dim=CONFIG["model_dim"], 
                                   num_heads=CONFIG["num_heads"], 
                                   num_layers=CONFIG["num_layers"])
    
    bounded_model = BoundedMemoryModel(patch_size=CONFIG["patch_size"], 
                                        dim=CONFIG["model_dim"], 
                                        num_heads=CONFIG["num_heads"], 
                                        num_layers=CONFIG["num_layers"])
    
    results = []
    
    # Evaluate on each domain
    for domain in CONFIG["domains"]:
        print(f"\nEvaluating on domain: {domain}")
        
        # Create dataloaders
        train_loader = DataLoader(datasets[domain]["train"], batch_size=CONFIG["batch_size"], shuffle=True)
        val_loader = DataLoader(datasets[domain]["val"], batch_size=CONFIG["batch_size"])
        test_loader = DataLoader(datasets[domain]["test"], batch_size=CONFIG["batch_size"])
        
        # Train Full-Context model
        print("Training Full-Context model...")
        train_model(full_model, train_loader, val_loader, CONFIG["num_epochs"], device)
        full_mae = compute_mae(full_model, test_loader, device)
        
        # Train Bounded-Memory model
        print("Training Bounded-Memory model...")
        train_model(bounded_model, train_loader, val_loader, CONFIG["num_epochs"], device)
        bounded_mae = compute_mae(bounded_model, test_loader, device)
        
        results.append({
            "domain": domain,
            "full_context_mae": full_mae,
            "bounded_memory_mae": bounded_mae
        })
        
        print(f"  Full-Context MAE: {full_mae:.4f}")
        print(f"  Bounded-Memory MAE: {bounded_mae:.4f}")
    
    # Save results
    results_df = []
    for r in results:
        results_df.append(r)
    
    with open("data/results.csv", "w") as f:
        f.write("domain,full_context_mae,bounded_memory_mae\n")
        for r in results:
            f.write(f"{r['domain']},{r['full_context_mae']:.6f},{r['bounded_memory_mae']:.6f}\n")
    
    print("\nSaved results to data/results.csv")
    
    # Plot comparison
    domains = [r["domain"] for r in results]
    full_mae = [r["full_context_mae"] for r in results]
    bounded_mae = [r["bounded_memory_mae"] for r in results]
    
    plt.figure(figsize=(10, 6))
    x = np.arange(len(domains))
    width = 0.35
    
    plt.bar(x - width/2, full_mae, width, label='Full-Context', color='skyblue')
    plt.bar(x + width/2, bounded_mae, width, label='Bounded-Memory', color='salmon')
    
    plt.xlabel('Domain')
    plt.ylabel('Mean Absolute Error (MAE)')
    plt.title('SpatialBench CPU Adaptation: Model Performance Comparison')
    plt.xticks(x, domains)
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("figures/comparison.png", dpi=150)
    plt.close()
    
    print("Saved comparison plot to figures/comparison.png")
    print("\nAdaptation complete. All artifacts written.")

if __name__ == "__main__":
    main()
