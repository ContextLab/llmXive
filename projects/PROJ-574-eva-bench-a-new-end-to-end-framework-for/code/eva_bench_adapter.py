import os
import json
import random
import csv
import time
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

# Ensure directories exist
os.makedirs("data", exist_ok=True)
os.makedirs("figures", exist_ok=True)

# Set random seed for reproducibility
random.seed(42)
np.random.seed(42)

print("EVA-Bench Adapter: CPU-Tractable Simulation & Evaluation")
print("-" * 50)

# --- CONFIGURATION (Scaled Down for CPU/Time Constraints) ---
# Original: 213 scenarios, 12 systems, complex audio simulation
# Adaptation: 20 scenarios, 3 proxy "systems", synthetic text/audio metrics
NUM_SCENARIOS = 20
NUM_SYSTEMS = 3
SYSTEM_NAMES = ["System_A_Light", "System_B_Small", "System_C_Cpu"]
DOMAINS = ["Customer Support", "Banking", "Healthcare"]

# --- STEP 1: SIMULATE CONVERSATIONS (Bot-to-Bot Proxy) ---
# Original: Audio simulation, STT/TTS loops, dynamic dialogue
# Adaptation: Text-based dialogue simulation with injected noise/accent factors

def generate_synthetic_dialogue(scenario_id, domain):
    """Generates a simplified conversation log with simulated audio metrics."""
    turns = random.randint(3, 8)
    dialogue = []
    task_complete = random.choice([True, False]) # 50% base rate
    
    # Simulate audio quality degradation based on "accent" and "noise"
    noise_level = random.uniform(0, 0.5) # 0 to 0.5
    accent_factor = random.choice([0.0, 0.2, 0.4]) # None, Mild, Strong
    
    # Simulate turn-taking timing (in seconds)
    turn_times = [random.uniform(0.5, 2.5) for _ in range(turns)]
    total_duration = sum(turn_times)
    
    # Simulate "Speech Fidelity" (0-1) based on noise/accent
    fidelity = max(0.0, 1.0 - (noise_level * 0.6) - (accent_factor * 0.3))
    
    # Simulate "Faithfulness" (0-1) - did the bot stay on topic?
    faithfulness = max(0.0, min(1.0, 0.8 + random.uniform(-0.2, 0.2) - (noise_level * 0.1)))
    
    return {
        "scenario_id": scenario_id,
        "domain": domain,
        "turns": turns,
        "duration_sec": round(total_duration, 2),
        "noise_level": round(noise_level, 3),
        "accent_factor": accent_factor,
        "task_complete": task_complete,
        "fidelity": round(fidelity, 3),
        "faithfulness": round(faithfulness, 3),
        "turn_times": turn_times
    }

print("Generating synthetic conversations...")
conversations = []
for i in range(NUM_SCENARIOS):
    domain = random.choice(DOMAINS)
    conv = generate_synthetic_dialogue(i, domain)
    conversations.append(conv)

# Save raw simulation data
with open("data/simulated_conversations.json", "w") as f:
    json.dump(conversations, f, indent=2)
print(f"Saved {len(conversations)} simulated conversations to data/simulated_conversations.json")

# --- STEP 2: EVALUATE SYSTEMS (Proxy Metrics) ---
# Original: EVA-A (Accuracy), EVA-X (Experience), pass@1, pass@k
# Adaptation: Calculate composite scores based on simulated metrics

def calculate_eva_a(conv, system_idx):
    """
    EVA-A (Accuracy): Task Completion + Faithfulness + Fidelity
    System performance varies slightly based on system_idx to simulate differences.
    """
    # Base performance
    task_score = 1.0 if conv["task_complete"] else 0.0
    
    # System-specific modifiers (simulating architecture differences)
    # System A: Good at task, weak on audio
    # System B: Balanced
    # System C: Strong on audio, weaker on complex tasks
    if system_idx == 0: # System A
        task_mult = 1.0
        fidelity_mult = 0.8
    elif system_idx == 1: # System B
        task_mult = 0.9
        fidelity_mult = 1.0
    else: # System C
        task_mult = 0.85
        fidelity_mult = 1.1
    
    fidelity_score = conv["fidelity"] * fidelity_mult
    faithfulness_score = conv["faithfulness"] * 1.0 # Neutral
    
    # Composite: Weighted average
    score = (0.5 * task_score) + (0.25 * fidelity_score) + (0.25 * faithfulness_score)
    return min(1.0, max(0.0, score))

def calculate_eva_x(conv, system_idx):
    """
    EVA-X (Experience): Turn-taking, Conciseness (inverse of duration), Flow
    """
    # Conciseness: Shorter is better (normalized)
    conciseness = max(0, 1.0 - (conv["duration_sec"] / 15.0)) 
    
    # Turn-taking: Standard deviation of turn times (lower is better, more consistent)
    if len(conv["turn_times"]) > 1:
        turn_std = np.std(conv["turn_times"])
        turn_score = max(0, 1.0 - turn_std)
    else:
        turn_score = 0.5
        
    # System modifiers
    if system_idx == 0: # System A: Fast but choppy
        turn_mult = 0.8
    elif system_idx == 1: # System B: Balanced
        turn_mult = 1.0
    else: # System C: Slow but smooth
        turn_mult = 1.05
        
    score = (0.5 * conciseness) + (0.5 * turn_score * turn_mult)
    return min(1.0, max(0.0, score))

print("Evaluating systems on simulated data...")
results = []

for sys_idx, sys_name in enumerate(SYSTEM_NAMES):
    for conv in conversations:
        eva_a = calculate_eva_a(conv, sys_idx)
        eva_x = calculate_eva_x(conv, sys_idx)
        
        results.append({
            "system": sys_name,
            "scenario_id": conv["scenario_id"],
            "domain": conv["domain"],
            "eva_a": round(eva_a, 4),
            "eva_x": round(eva_x, 4),
            "noise_level": conv["noise_level"],
            "accent_factor": conv["accent_factor"]
        })

# Save evaluation results
with open("data/evaluation_results.csv", "w", newline='') as f:
    writer = csv.DictWriter(f, fieldnames=["system", "scenario_id", "domain", "eva_a", "eva_x", "noise_level", "accent_factor"])
    writer.writeheader()
    writer.writerows(results)
print(f"Saved evaluation results to data/evaluation_results.csv")

# --- STEP 3: AGGREGATE METRICS & VISUALIZATION ---
# Original: pass@1, pass@k, robustness gaps
# Adaptation: Mean scores, robustness gap (High Noise vs Low Noise)

print("Calculating aggregate metrics...")
aggregates = {}
for sys_name in SYSTEM_NAMES:
    sys_data = [r for r in results if r["system"] == sys_name]
    
    mean_a = np.mean([r["eva_a"] for r in sys_data])
    mean_x = np.mean([r["eva_x"] for r in sys_data])
    
    # Robustness Gap: Mean EVA-A for High Noise (>0.3) vs Low Noise (<0.1)
    high_noise = [r["eva_a"] for r in sys_data if r["noise_level"] > 0.3]
    low_noise = [r["eva_a"] for r in sys_data if r["noise_level"] < 0.1]
    
    gap_a = (np.mean(low_noise) - np.mean(high_noise)) if high_noise and low_noise else 0.0
    
    aggregates[sys_name] = {
        "eva_a_mean": round(mean_a, 4),
        "eva_x_mean": round(mean_x, 4),
        "robustness_gap": round(gap_a, 4)
    }

# Save aggregates
with open("data/aggregated_metrics.json", "w") as f:
    json.dump(aggregates, f, indent=2)
print("Saved aggregated metrics to data/aggregated_metrics.json")

# --- PLOTTING ---
print("Generating plots...")

# Plot 1: EVA-A vs EVA-X Scatter
plt.figure(figsize=(8, 6))
colors = {'System_A_Light': 'blue', 'System_B_Small': 'green', 'System_C_Cpu': 'red'}
for sys_name in SYSTEM_NAMES:
    sys_data = [r for r in results if r["system"] == sys_name]
    xs = [r["eva_a"] for r in sys_data]
    ys = [r["eva_x"] for r in sys_data]
    plt.scatter(xs, ys, label=sys_name, color=colors[sys_name], alpha=0.6, s=50)

plt.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5, label='Threshold 0.5')
plt.axvline(x=0.5, color='gray', linestyle='--', alpha=0.5)
plt.xlabel('EVA-A (Accuracy)')
plt.ylabel('EVA-X (Experience)')
plt.title('EVA-Bench Adapter: System Performance (Scaled Down)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("figures/eva_performance.png", dpi=150)
plt.close()
print("Saved plot to figures/eva_performance.png")

# Plot 2: Robustness Gap Bar Chart
plt.figure(figsize=(8, 6))
sys_names = list(aggregates.keys())
gaps = [aggregates[s]["robustness_gap"] for s in sys_names]
plt.bar(sys_names, gaps, color=['blue', 'green', 'red'])
plt.ylabel('Robustness Gap (EVA-A: Low Noise - High Noise)')
plt.title('Impact of Noise Perturbations on Accuracy')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("figures/robustness_gap.png", dpi=150)
plt.close()
print("Saved plot to figures/robustness_gap.png")

print("-" * 50)
print("Adapter execution complete.")
print("Outputs generated:")
print("  - data/simulated_conversations.json")
print("  - data/evaluation_results.csv")
print("  - data/aggregated_metrics.json")
print("  - figures/eva_performance.png")
print("  - figures/robustness_gap.png")

# Print summary to stdout for quick verification
print("\nSummary of Aggregated Metrics:")
for sys, vals in aggregates.items():
    print(f"  {sys}: EVA-A={vals['eva_a_mean']:.3f}, EVA-X={vals['eva_x_mean']:.3f}, Robustness Gap={vals['robustness_gap']:.3f}")

# Verify no system exceeds 0.5 on both (as per paper finding 1)
print("\nVerifying Paper Finding #1 (No system > 0.5 on both):")
for sys, vals in aggregates.items():
    if vals['eva_a_mean'] > 0.5 and vals['eva_x_mean'] > 0.5:
        print(f"  WARNING: {sys} exceeds 0.5 on both (unexpected in this simulation).")
    else:
        print(f"  OK: {sys} respects the constraint.")
