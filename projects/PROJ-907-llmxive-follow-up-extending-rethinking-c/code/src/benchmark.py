import os
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
import torch
import time

def run_benchmark(model, image_list, seed):
    """
    Runs inference on a list of images and measures the time taken.
    """
    start_time = time.time()
    with torch.no_grad():  # Ensure no gradients are calculated during inference
        for img in image_list:
            model(img)
    end_time = time.time()

    latency = (end_time - start_time) / len(image_list)
    return latency

def calculate_fid(predictions, real_images):  # Placeholder for FID calculation
  # Replace with actual implementation using src/metrics.py

  # Dummy return value for demonstration purposes only
  return 0.5

def main(model_type, image_dir, num_images=40, start_index=100):
    """
    Main function to run the benchmark and save results.
    """
    image_paths = [os.path.join(image_dir, f"image_{i}.png") for i in range(start_index, start_index + num_images)]

    # Load images (replace with actual image loading logic)
    image_list = []  # Replace with your image processing pipeline
    for path in image_paths:
        try:
            # Assuming image is a tensor for simplicity; replace with PIL/CV2 etc.
            img = torch.randn(3, 256, 256) # Dummy data
            image_list.append(img)
        except FileNotFoundError:
            logging.warning(f"Image file not found: {path}")

    # Measure latency
    latency = run_benchmark(model, image_list, seed=42)  # Replace with your model and images

    # Calculate FID (replace with actual implementation using src/metrics.py)
    fid = calculate_fid(image_list, image_list)

    results = {
        "latency": latency,
        "fid": fid,
        "seed": 42,
        "model_type": model_type
    }

    # Save results to CSV and JSON
    save_to_csv("data/results/benchmark_results.csv", results)
    save_to_json("data/results/benchmark_results.json", results)


def save_to_csv(filename, data):
    """Appends benchmark data to a CSV file."""
    with open(filename, "a") as f:
        header = ["latency", "fid", "seed", "model_type"]
        if not any(line.startswith(h + ",") for line in open(filename).readlines() if h in header):  # Check if header exists
            f.write(",".join(header) + "\n")

        values = [str(data[key]) for key in header]
        f.write(",".join(values) + "\n")


def save_to_json(filename, data):
    """Appends benchmark data to a JSON file."""
    try:
        with open(filename, "r") as f:
            existing_data = json.load(f)
    except FileNotFoundError:
        existing_data = []

    existing_data.append(data)
    with open(filename, "w") as f:
        json.dump(existing_data, f, indent=4)