import os
import json
import time
import numpy as np
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm
from datasets import load_dataset
from PIL import Image
from torchvision import transforms
from sklearn.metrics import mean_squared_error, mean_absolute_error

# Configuration
SAMPLE_SIZE = 50  # Small sample for CPU speed
NOISE_STD = 0.1   # Standard deviation for synthetic noise
DEVICE = "cpu"
BATCH_SIZE = 8
EPOCHS = 5        # Few epochs for quick CPU training
IMAGE_SIZE = 64   # Resize to small size for speed

# Paths
DATA_DIR = "data"
FIGURES_DIR = "figures"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

# 1. Data Loading & Preprocessing
print("Loading small sample of NYU Depth V2 dataset...")
try:
    # Load a tiny subset of NYU Depth V2 (RGB + Depth)
    # Using 'nyu_depth_v2' from huggingface datasets
    dataset = load_dataset("nielsr/nyu-depth-v2", split="train", trust_remote_code=True)
    # Select a small random sample
    indices = np.random.choice(len(dataset), SAMPLE_SIZE, replace=False)
    sample_data = dataset.select(indices)
    
    # Transform
    transform = transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ToTensor()
    ])

    class NyuDepthDataset(Dataset):
        def __init__(self, dataset, transform):
            self.dataset = dataset
            self.transform = transform

        def __len__(self):
            return len(self.dataset)

        def __getitem__(self, idx):
            item = self.dataset[idx]
            # item contains 'image' (RGB) and 'depth' (depth map)
            img = item['image']
            depth = item['depth']
            
            img_t = self.transform(img)
            depth_t = self.transform(depth.convert('L')) # Convert depth to grayscale tensor
            
            return img_t, depth_t.squeeze(0), item['image'] # Return tensor and original for saving

    nyu_dataset = NyuDepthDataset(sample_data, transform)
    loader = DataLoader(nyu_dataset, batch_size=BATCH_SIZE, shuffle=True)
    print(f"Loaded {len(nyu_dataset)} samples.")
except Exception as e:
    print(f"Error loading dataset: {e}")
    print("Attempting fallback to local generation if possible, but failing honestly is preferred.")
    raise RuntimeError("Could not load real data. Failing as per constraints.")

# 2. Model Definition (Tiny Denoising Autoencoder)
# Replaces the heavy diffusion model with a small MLP for CPU feasibility
class TinyDenoiser(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, input_dim),
            nn.Sigmoid() # Output in [0, 1] assuming normalized depth
        )
    
    def forward(self, x):
        # Flatten, denoise, reshape
        batch_size = x.shape[0]
        x_flat = x.view(batch_size, -1)
        out = self.net(x_flat)
        return out.view(batch_size, 1, IMAGE_SIZE, IMAGE_SIZE)

# 3. Noise Simulation
def add_noise(depth_tensor, std=NOISE_STD):
    noise = torch.randn_like(depth_tensor) * std
    noisy = depth_tensor + noise
    # Clip to [0, 1] to simulate realistic bounded sensor noise
    return torch.clamp(noisy, 0.0, 1.0)

# 4. Training Loop
print("Training Tiny Denoiser on CPU...")
model = TinyDenoiser(input_dim=IMAGE_SIZE * IMAGE_SIZE).to(DEVICE)
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
criterion = nn.MSELoss()

start_time = time.time()
for epoch in range(EPOCHS):
    model.train()
    epoch_loss = 0.0
    for batch_imgs, batch_depths, _ in tqdm(loader, desc=f"Epoch {epoch+1}/{EPOCHS}"):
        batch_depths = batch_depths.to(DEVICE)
        # Create noisy version
        noisy_depths = add_noise(batch_depths)
        
        optimizer.zero_grad()
        # Predict clean from noisy
        predictions = model(noisy_depths)
        
        loss = criterion(predictions, batch_depths)
        loss.backward()
        optimizer.step()
        
        epoch_loss += loss.item()
    
    avg_loss = epoch_loss / len(loader)
    print(f"Epoch {epoch+1}, Loss: {avg_loss:.4f}")

training_time = time.time() - start_time
print(f"Training completed in {training_time:.2f}s")

# 5. Evaluation & Artifact Generation
print("Generating evaluation artifacts...")
model.eval()
results = []
all_gt = []
all_noisy = []
all_pred = []

# Save a few samples for visualization
sample_indices_to_save = [0, 1, 2]
fig, axes = plt.subplots(len(sample_indices_to_save), 3, figsize=(12, 12 * len(sample_indices_to_save)))
if len(sample_indices_to_save) == 1:
    axes = axes.reshape(1, -1)

sample_count = 0

with torch.no_grad():
    for batch_imgs, batch_depths, orig_imgs in loader:
        batch_depths = batch_depths.to(DEVICE)
        noisy_depths = add_noise(batch_depths)
        denoised = model(noisy_depths)
        
        # Convert to numpy for metrics
        gt_np = batch_depths.cpu().numpy()
        noisy_np = noisy_depths.cpu().numpy()
        pred_np = denoised.cpu().numpy()
        
        all_gt.append(gt_np)
        all_noisy.append(noisy_np)
        all_pred.append(pred_np)
        
        # Save specific samples
        for i in range(len(batch_depths)):
            if sample_count in sample_indices_to_save:
                idx_in_batch = i
                gt_map = gt_np[idx_in_batch, 0]
                noisy_map = noisy_np[idx_in_batch, 0]
                pred_map = pred_np[idx_in_batch, 0]
                
                row_idx = sample_indices_to_save.index(sample_count)
                # GT
                axes[row_idx, 0].imshow(gt_map, cmap='viridis')
                axes[row_idx, 0].set_title("Ground Truth Depth")
                axes[row_idx, 0].axis('off')
                # Noisy
                axes[row_idx, 1].imshow(noisy_map, cmap='viridis')
                axes[row_idx, 1].set_title(f"Noisy (σ={NOISE_STD})")
                axes[row_idx, 1].axis('off')
                # Denoised
                axes[row_idx, 2].imshow(pred_map, cmap='viridis')
                axes[row_idx, 2].set_title("Denoised (Tiny-MLP)")
                axes[row_idx, 2].axis('off')
            
            sample_count += 1
            if sample_count >= len(sample_indices_to_save):
                break
        if sample_count >= len(sample_indices_to_save):
            break

plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, "denoising_comparison.png"), dpi=150)
plt.close()
print(f"Saved figure: {FIGURES_DIR}/denoising_comparison.png")

# Aggregate Metrics
all_gt = np.concatenate(all_gt, axis=0)
all_noisy = np.concatenate(all_noisy, axis=0)
all_pred = np.concatenate(all_pred, axis=0)

# Flatten for metrics
gt_flat = all_gt.flatten()
noisy_flat = all_noisy.flatten()
pred_flat = all_pred.flatten()

# Calculate metrics
rmse_noisy = np.sqrt(mean_squared_error(gt_flat, noisy_flat))
mae_noisy = mean_absolute_error(gt_flat, noisy_flat)

rmse_pred = np.sqrt(mean_squared_error(gt_flat, pred_flat))
mae_pred = mean_absolute_error(gt_flat, pred_flat)

# Improvement
rmse_improvement = rmse_noisy - rmse_pred
mae_improvement = mae_noisy - mae_pred

metrics = {
    "dataset": "NYU Depth V2 (Sample: 50 images)",
    "noise_std": NOISE_STD,
    "model": "Tiny Denoising Autoencoder (3-layer MLP)",
    "training_time_sec": training_time,
    "metrics": {
        "noisy_input": {
            "rmse": float(rmse_noisy),
            "mae": float(mae_noisy)
        },
        "denoised_output": {
            "rmse": float(rmse_pred),
            "mae": float(mae_pred)
        },
        "improvement": {
            "rmse_delta": float(rmse_improvement),
            "mae_delta": float(mae_improvement)
        }
    },
    "note": "Approximation: Replaced Diffusion with MLP Denoiser for CPU tractability."
}

# Save JSON
with open(os.path.join(DATA_DIR, "denoised_results.json"), "w") as f:
    json.dump(metrics, f, indent=2)
print(f"Saved metrics: {DATA_DIR}/denoised_results.json")

# Save CSV summary (first 100 pixels stats for sanity check)
summary_data = []
for i in range(min(100, len(gt_flat))):
    summary_data.append({
        "pixel_idx": i,
        "gt": float(gt_flat[i]),
        "noisy": float(noisy_flat[i]),
        "denoised": float(pred_flat[i])
    })

import pandas as pd
df = pd.DataFrame(summary_data)
df.to_csv(os.path.join(DATA_DIR, "noisy_depths.csv"), index=False)
print(f"Saved sample data: {DATA_DIR}/noisy_depths.csv")

print("\n--- Execution Summary ---")
print(f"Total Runtime: {time.time() - start_time:.2f}s")
print(f"RMSE Improvement: {rmse_improvement:.4f} (Lower is better)")
print("Artifacts written successfully.")
