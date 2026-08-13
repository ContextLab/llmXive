import os
import json
import hashlib
import logging
import gc
import time
from pathlib import Path
import torch

def get_memory_usage_gb():
    """Returns memory usage in GB."""
    with open('/proc/meminfo', 'r') as meminfo:
        meminfo_lines = meminfo.readlines()
        total_memory_line = next((line for line in meminfo_lines if "MemTotal" in line), None)
        if total_memory_line:
            total_memory_kb = int(total_memory_line.split(":")[1].strip().split(" ")[0])
            total_memory_gb = total_memory_kb / (1024 * 1024)
            return total_memory_gb
    return None

def compute_data_source_hash(file_path):
  """Computes the SHA-256 hash of a file."""
  sha256_hash = hashlib.sha256()
  with open(file_path, "rb") as f:
      for byte_block in iter(lambda: f.read(4096), b""):
          sha256_hash.update(byte_block)
  return sha256_hash.hexdigest()

def log_data_source_verification(file_path, hash_value):
    """Logs data source verification information."""
    logging.info(f"Verified file: {file_path}, SHA-256 Hash: {hash_value}")


def trace_single_image(model, image, timestep):
  """Traces a single image for a given timestep."""
  with torch.no_grad():  # Ensure no gradients are computed during tracing
      output = model(image, timestep=timestep)
  return output

def trace_routing_batch(model, images, timesteps):
    """Traces routing weights for a batch of images and timesteps."""
    outputs = []
    for image, timestep in zip(images, timesteps):
        output = trace_single_image(model, image, timestep)
        outputs.append(output)
    return outputs

def trace_routing(model, dataset, trace_set_size, random_seed):
  """Traces routing weights for a given dataset."""
  torch.manual_seed(random_seed)
  routing_tensors = []
  for i in range(trace_set_size):
    image = dataset[i]  # Assuming the dataset provides images directly
    timestep = torch.randint(0, 1000, (1,)) #linear spacing between 0 and 1000
    output = trace_single_image(model, image, timestep)
    routing_tensors.append(output)

  return routing_tensors


def simulate_routing_trace(model, num_images=100):
  """Simulates a routing trace for testing."""
  # Placeholder for actual tracing logic
  dummy_data = [torch.randn(3, 256, 256) for _ in range(num_images)]
  return dummy_data

def main():
    pass  # Replace with the main execution logic if needed
