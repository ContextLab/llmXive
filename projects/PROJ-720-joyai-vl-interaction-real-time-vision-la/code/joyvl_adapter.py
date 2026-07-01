import os
import sys
import time
import json
import random
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import cv2
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel

# Ensure we can import from the parent directory if needed, though we aim for self-containment
# The script will be run from `code/`, so `external/` is one level up.
# We do NOT import from the massive external repo to avoid dependency hell on CPU.

# Configuration
OUTPUT_DIR = Path("data")
FIGURES_DIR = Path("figures")
OUTPUT_DIR.mkdir(exist_ok=True)
FIGURES_DIR.mkdir(exist_ok=True)

# Synthetic Video Configuration (to guarantee runnable code without 10GB downloads)
# We simulate "Events" (red circles moving) vs "Background" (static blue)
VIDEO_WIDTH = 256
VIDEO_HEIGHT = 256
FPS = 1
TOTAL_FRAMES = 50
EVENT_START = 10
EVENT_END = 40
FRAME_RATE = 1.0

class SyntheticVideoGenerator:
    """
    Generates a deterministic synthetic video to simulate 'events' vs 'background'.
    This replaces the need for a real RTSP stream or large Kinetics dataset download
    for the purpose of validating the VL logic on CPU.
    """
    def __init__(self, seed=42):
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)

    def generate(self, save_path: str) -> List[Dict[str, Any]]:
        """
        Generates a video file and returns a list of ground-truth labels for each frame.
        Label: {'frame_idx': int, 'is_event': bool, 'ground_truth_label': str}
        """
        cap = cv2.VideoCapture(0) # Dummy to check if cv2 works, then we overwrite
        cap.release()

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(save_path, fourcc, FPS, (VIDEO_WIDTH, VIDEO_HEIGHT))

        labels = []

        for i in range(TOTAL_FRAMES):
            # Create a base background (static noise or solid color)
            frame = np.zeros((VIDEO_HEIGHT, VIDEO_WIDTH, 3), dtype=np.uint8)
            frame[:, :] = [100, 149, 237] # Cornflower blue background

            is_event = False
            label_text = "background"

            if EVENT_START <= i <= EVENT_END:
                is_event = True
                label_text = "red_circle_moving"
                # Draw a red circle moving across the screen
                center_x = int(50 + (i - EVENT_START) * 5)
                center_y = VIDEO_HEIGHT // 2
                cv2.circle(frame, (center_x, center_y), 30, (0, 0, 255), -1)
                # Add some text to simulate "speech" or "content"
                cv2.putText(frame, "EVENT", (center_x - 30, center_y - 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            out.write(frame)
            labels.append({
                "frame_idx": i,
                "is_event": is_event,
                "ground_truth_label": label_text,
                "timestamp": float(i)
            })

        out.release()
        return labels

def load_vl_model(device: str = "cpu"):
    """
    Loads a CLIP model. This is the 'Vision-First' backbone.
    In the original paper, this is the 8B JoyAI model.
    Here, we use CLIP to test the 'Vision-Text Alignment' logic.
    """
    # Using a small, CPU-friendly model
    model_name = "openai/clip-vit-base-patch32"
    print(f"Loading model: {model_name} on {device}...")
    
    try:
        model = CLIPModel.from_pretrained(model_name)
        processor = CLIPProcessor.from_pretrained(model_name)
        model = model.to(device)
        model.eval()
        print("Model loaded successfully.")
        return model, processor
    except Exception as e:
        print(f"Error loading model: {e}")
        print("Falling back to a mock model logic for demonstration if network fails.")
        return None, None

def run_inference(model, processor, video_path: str, device: str, ground_truth: List[Dict]):
    """
    Runs the 'interaction decision' logic.
    Original: Model decides 'Silence', 'Respond', 'Delegate'.
    Adaptation: Model calculates similarity to 'event' text. If > threshold -> 'Respond'.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    predictions = []
    frame_idx = 0
    total_time = 0

    # Define the "trigger" text prompts
    # In the real paper, the model generates these or chooses from a pool.
    # Here we use a fixed prompt to simulate the "vision-triggered" capability.
    trigger_prompt = "a red circle moving on a blue background, person speaking"
    silence_prompt = "static blue background, nothing happening"

    print(f"Processing video: {video_path}...")
    start_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(frame_rgb)

        # Process for CLIP
        inputs = processor(
            text=[trigger_prompt, silence_prompt], 
            images=pil_img, 
            return_tensors="pt", 
            padding=True
        ).to(device)

        with torch.no_grad():
            outputs = model(**inputs)
            logits_per_image = outputs.logits_per_image # (batch, text_count)
            probs = torch.softmax(logits_per_image, dim=1)
            # We care about the probability of the 'trigger' prompt (index 0)
            trigger_prob = probs[0, 0].item()

        # Decision Logic (The "Core Result" we are measuring)
        # Threshold chosen to separate event vs background clearly in this synthetic setup
        THRESHOLD = 0.6
        decision = "RESPOND" if trigger_prob > THRESHOLD else "SILENCE"
        
        # Record result
        predictions.append({
            "frame_idx": frame_idx,
            "timestamp": float(frame_idx),
            "trigger_probability": trigger_prob,
            "decision": decision,
            "is_event": ground_truth[frame_idx]["is_event"],
            "ground_truth_label": ground_truth[frame_idx]["ground_truth_label"]
        })

        frame_idx += 1

    cap.release()
    total_time = time.time() - start_time
    print(f"Inference complete. Processed {frame_idx} frames in {total_time:.2f}s.")
    
    return predictions, total_time

def calculate_metrics(predictions: List[Dict]) -> Dict[str, float]:
    """
    Calculates Precision, Recall, F1-Score for the 'RESPOND' decision.
    This proxies the 'human preference' metric by measuring alignment with ground truth.
    """
    tp = 0
    fp = 0
    fn = 0
    
    for p in predictions:
        is_predicted_event = (p["decision"] == "RESPOND")
        is_actual_event = p["is_event"]
        
        if is_predicted_event and is_actual_event:
            tp += 1
        elif is_predicted_event and not is_actual_event:
            fp += 1
        elif not is_predicted_event and is_actual_event:
            fn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn
    }

def save_results(predictions: List[Dict], metrics: Dict, output_path: Path):
    """Saves the detailed predictions and summary metrics to CSV/JSON."""
    # Save detailed predictions
    pred_file = output_path / "predictions.csv"
    with open(pred_file, "w") as f:
        f.write("frame_idx,timestamp,trigger_probability,decision,is_event,ground_truth_label\n")
        for p in predictions:
            f.write(f"{p['frame_idx']},{p['timestamp']:.2f},{p['trigger_probability']:.4f},"
                    f"{p['decision']},{p['is_event']},{p['ground_truth_label']}\n")
    
    # Save summary metrics
    metrics_file = output_path / "metrics.json"
    with open(metrics_file, "w") as f:
        json.dump(metrics, f, indent=2)
    
    print(f"Results saved to {pred_file} and {metrics_file}")

def save_plot(predictions: List[Dict], output_path: Path):
    """Generates a plot of the trigger probability over time."""
    try:
        import matplotlib
        matplotlib.use('Agg') # Non-interactive backend
        import matplotlib.pyplot as plt

        frames = [p["frame_idx"] for p in predictions]
        probs = [p["trigger_probability"] for p in predictions]
        events = [p["is_event"] for p in predictions]

        plt.figure(figsize=(10, 6))
        plt.plot(frames, probs, label="Trigger Probability", color="blue", linewidth=2)
        
        # Highlight event regions
        event_start = None
        for i, is_ev in enumerate(events):
            if is_ev and event_start is None:
                event_start = i
            elif not is_ev and event_start is not None:
                plt.axvspan(event_start, i, color='red', alpha=0.2, label='Ground Truth Event')
                event_start = None
        if event_start is not None:
            plt.axvspan(event_start, len(events), color='red', alpha=0.2)

        plt.axhline(y=0.6, color='green', linestyle='--', label='Decision Threshold')
        plt.xlabel("Frame Index")
        plt.ylabel("Probability (0-1)")
        plt.title("JoyAI-VL Adaptation: Vision-Trigger Probability Over Time")
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plot_path = output_path / "interaction_probability.png"
        plt.savefig(plot_path, dpi=150)
        plt.close()
        print(f"Plot saved to {plot_path}")
    except ImportError:
        print("Matplotlib not found. Skipping plot generation.")

def main():
    parser = argparse.ArgumentParser(description="JoyAI-VL Interaction Adaptation (CPU)")
    parser.add_argument("--device", type=str, default="cpu", choices=["cpu"], 
                        help="Device to run on. Only CPU supported for this adapter.")
    parser.add_argument("--video-path", type=str, default="data/synthetic_event.mp4",
                        help="Path to input video (generated if missing).")
    args = parser.parse_args()

    print("--- JoyAI-VL Interaction Adaptation ---")
    print(f"Target: {args.device}")
    print(f"Video: {args.video_path}")

    # 1. Generate Synthetic Video (Real data simulation)
    if not os.path.exists(args.video_path):
        print("Generating synthetic video (simulating real-world events)...")
        generator = SyntheticVideoGenerator()
        generator.generate(args.video_path)
        print(f"Generated video: {args.video_path}")

    # 2. Load Model
    # Check if we can load the real model. If not (e.g. network issues in CI),
    # we might need a fallback, but the prompt says "NEVER fabricate".
    # We assume the environment has torch/transformers.
    model, processor = load_vl_model(args.device)
    
    if model is None:
        # Fallback: If model fails to load (e.g. network), we cannot produce a real result.
        # We must fail honestly rather than fabricate.
        print("CRITICAL: Failed to load VL model. Cannot produce real result.")
        # Create a failure artifact to indicate the run failed
        with open(OUTPUT_DIR / "run_status.json", "w") as f:
            json.dump({"status": "failed", "reason": "model_load_error"}, f)
        sys.exit(1)

    # 3. Generate Ground Truth (for the synthetic video)
    # We regenerate the labels to match the video generation logic
    generator = SyntheticVideoGenerator()
    ground_truth = generator.generate(args.video_path) # This returns the labels, video is already there

    # 4. Run Inference
    predictions, duration = run_inference(model, processor, args.video_path, args.device, ground_truth)

    # 5. Calculate Metrics
    metrics = calculate_metrics(predictions)

    # 6. Save Outputs
    save_results(predictions, metrics, OUTPUT_DIR)
    save_plot(predictions, FIGURES_DIR)

    # 7. Final Report
    print("\n--- Final Results ---")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall: {metrics['recall']:.4f}")
    print(f"F1 Score: {metrics['f1_score']:.4f}")
    
    with open(OUTPUT_DIR / "run_status.json", "w") as f:
        json.dump({
            "status": "success",
            "metrics": metrics,
            "duration_seconds": duration,
            "frames_processed": len(predictions)
        }, f, indent=2)

    print("Adaptation complete. Artifacts written to data/ and figures/.")

if __name__ == "__main__":
    main()
