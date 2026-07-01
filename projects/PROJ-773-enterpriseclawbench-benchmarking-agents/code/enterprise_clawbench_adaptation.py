import json
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Tuple

import matplotlib.pyplot as plt
import pandas as pd

# Ensure directories exist
DATA_DIR = Path("data")
FIGURES_DIR = Path("figures")
DATA_DIR.mkdir(exist_ok=True)
FIGURES_DIR.mkdir(exist_ok=True)

# --- Configuration ---
RANDOM_SEED = 42
NUM_TASKS = 50
SKILL_DIMENSIONS = [
    "File Reading", "Code Generation", "Data Analysis", 
    "Web Search", "Tool Invocation", "Artifact Rendering"
]
ROLE_CLASSES = ["Analyst", "Developer", "Designer", "Manager"]
ARTIFACT_TYPES = ["HTML", "CSV", "Markdown", "JSON", "Image"]

# Mock Agent Skill Matrix (Deterministic for reproducibility)
# Represents a model that is good at some things, bad at others.
# This mimics the "Skill Transfer" analysis in the paper.
MOCK_SKILL_PROFILES = {
    "Analyst": {"File Reading": 0.95, "Data Analysis": 0.90, "Code Generation": 0.40, "Web Search": 0.80, "Tool Invocation": 0.60, "Artifact Rendering": 0.30},
    "Developer": {"File Reading": 0.85, "Data Analysis": 0.60, "Code Generation": 0.95, "Web Search": 0.70, "Tool Invocation": 0.85, "Artifact Rendering": 0.40},
    "Designer": {"File Reading": 0.70, "Data Analysis": 0.30, "Code Generation": 0.30, "Web Search": 0.60, "Tool Invocation": 0.50, "Artifact Rendering": 0.95},
    "Manager": {"File Reading": 0.80, "Data Analysis": 0.70, "Code Generation": 0.20, "Web Search": 0.90, "Tool Invocation": 0.75, "Artifact Rendering": 0.50}
}

def generate_synthetic_tasks(n: int, seed: int) -> List[Dict[str, Any]]:
    """
    Generates a small set of tasks mimicking the EnterpriseClawBench schema.
    Since real data is proprietary, we create a deterministic synthetic set
    to demonstrate the evaluation protocol.
    """
    random.seed(seed)
    tasks = []
    for i in range(n):
        role = random.choice(ROLE_CLASSES)
        skill = random.choice(SKILL_DIMENSIONS)
        artifact = random.choice(ARTIFACT_TYPES)
        difficulty = random.choice(["easy", "medium", "hard"])
        
        task = {
            "task_id": f"task_{i:04d}",
            "role_class": role,
            "skill_dimension": skill,
            "artifact_type": artifact,
            "difficulty": difficulty,
            "prompt": f"Simulated prompt for {role} to perform {skill} and output {artifact}.",
            "expected_artifact_path": f"/workspace/outputs/{artifact.lower()}_out_{i}",
            "rubric": {
                "must_include": [f"{skill} logic", f"{artifact} format"],
                "must_not_include": ["hallucinated data", "empty response"]
            }
        }
        tasks.append(task)
    return tasks

def mock_agent_execute(task: Dict[str, Any], profile: Dict[str, float]) -> Dict[str, Any]:
    """
    Simulates the agent execution. 
    Returns a result based on the skill profile (deterministic logic + small noise).
    """
    skill = task["skill_dimension"]
    base_prob = profile.get(skill, 0.5)
    
    # Add slight difficulty penalty
    difficulty_penalty = {"easy": 0.0, "medium": 0.1, "hard": 0.2}[task["difficulty"]]
    success_prob = max(0.0, base_prob - difficulty_penalty)
    
    # Deterministic success based on probability and task_id (seeded by task_id string hash)
    # This ensures if we run the script twice, we get the same results without external RNG state.
    task_hash = hash(task["task_id"]) % 100
    success = (task_hash % 100) < (success_prob * 100)
    
    # Simulate token usage based on success and difficulty
    tokens_input = random.randint(100, 500)
    tokens_output = random.randint(50, 200) if success else random.randint(10, 50)
    
    return {
        "task_id": task["task_id"],
        "success": success,
        "score": 1.0 if success else 0.0,
        "artifacts_generated": success,
        "tokens_input": tokens_input,
        "tokens_output": tokens_output,
        "total_tokens": tokens_input + tokens_output,
        "error": None if success else "Skill mismatch or logic failure"
    }

def run_evaluation_pipeline(tasks: List[Dict[str, Any]], profile_name: str = "Analyst") -> List[Dict[str, Any]]:
    """
    Runs the evaluation loop:
    1. Iterate tasks
    2. 'Run' agent (mock)
    3. Score result
    4. Aggregate stats
    """
    profile = MOCK_SKILL_PROFILES.get(profile_name, MOCK_SKILL_PROFILES["Analyst"])
    results = []
    
    for task in tasks:
        result = mock_agent_execute(task, profile)
        result["role_class"] = task["role_class"]
        result["skill_dimension"] = task["skill_dimension"]
        result["artifact_type"] = task["artifact_type"]
        result["difficulty"] = task["difficulty"]
        results.append(result)
        
    return results

def generate_heatmap_data(results: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Aggregates results into a matrix for the heatmap (Skill x Role).
    Matches Fig 5 / Fig 8 style from the paper.
    """
    df = pd.DataFrame(results)
    
    # Pivot table: Rows = Skill, Cols = Role, Values = Mean Success Rate
    pivot = df.groupby(["skill_dimension", "role_class"])["success"].mean().unstack(fill_value=0)
    return pivot

def generate_leaderboard_data(results: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Aggregates results for a leaderboard view (Role vs Avg Score).
    Matches Fig 4 style.
    """
    df = pd.DataFrame(results)
    stats = df.groupby("role_class").agg({
        "success": "mean",
        "total_tokens": "sum"
    }).reset_index()
    stats.columns = ["Role", "Success Rate", "Total Tokens"]
    stats = stats.sort_values("Success Rate", ascending=False)
    return stats

def plot_results(pivot_df: pd.DataFrame, leaderboard_df: pd.DataFrame, suffix: str = ""):
    """
    Creates the figures required by the paper's metrics.
    """
    # 1. Heatmap: Skill Transfer
    plt.figure(figsize=(10, 6))
    im = plt.imshow(pivot_df, cmap="viridis", aspect="auto")
    plt.xticks(range(len(pivot_df.columns)), pivot_df.columns, rotation=45, ha="right")
    plt.yticks(range(len(pivot_df.index)), pivot_df.index)
    plt.title(f"Skill Transfer Matrix ({suffix})")
    plt.colorbar(im, label="Success Rate")
    # Add text annotations
    for i in range(len(pivot_df.index)):
        for j in range(len(pivot_df.columns)):
            plt.text(j, i, f"{pivot_df.iloc[i, j]:.2f}", ha="center", va="center", color="white" if pivot_df.iloc[i, j] > 0.5 else "black")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / f"skill_transfer_heatmap_{suffix}.png", dpi=150)
    plt.close()

    # 2. Leaderbar: Role Performance
    plt.figure(figsize=(8, 5))
    plt.bar(leaderboard_df["Role"], leaderboard_df["Success Rate"], color="skyblue")
    plt.ylim(0, 1.0)
    plt.title(f"Agent Performance by Role ({suffix})")
    plt.ylabel("Success Rate")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / f"leaderboard_{suffix}.png", dpi=150)
    plt.close()

def main():
    print("Starting EnterpriseClawBench Adaptation (Scaled-Down Protocol)...")
    
    # 1. Generate Synthetic Tasks (Real data not available)
    print(f"Generating {NUM_TASKS} synthetic tasks...")
    tasks = generate_synthetic_tasks(NUM_TASKS, RANDOM_SEED)
    
    # Save raw tasks for verification
    with open(DATA_DIR / "synthetic_tasks.json", "w") as f:
        json.dump(tasks, f, indent=2)
    print(f"Saved synthetic tasks to {DATA_DIR / 'synthetic_tasks.json'}")

    # 2. Run Evaluation for multiple roles to show "Skill Transfer"
    # We simulate running the benchmark with different "Agent Configurations" (Roles)
    all_results = []
    summary_stats = []
    
    for role in ROLE_CLASSES:
        print(f"Evaluating agent configuration: {role}...")
        results = run_evaluation_pipeline(tasks, profile_name=role)
        all_results.extend(results)
        
        # Aggregate for summary
        avg_success = sum(1 for r in results if r["success"]) / len(results)
        total_cost = sum(r["total_tokens"] for r in results)
        summary_stats.append({
            "Role": role,
            "Success Rate": avg_success,
            "Total Cost (Tokens)": total_cost
        })

    # 3. Save Detailed Results
    results_df = pd.DataFrame(all_results)
    results_df.to_csv(DATA_DIR / "evaluation_results.csv", index=False)
    print(f"Saved detailed results to {DATA_DIR / 'evaluation_results.csv'}")

    # 4. Save Summary Stats (JSON)
    with open(DATA_DIR / "benchmark_summary.json", "w") as f:
        json.dump(summary_stats, f, indent=2)
    print(f"Saved summary stats to {DATA_DIR / 'benchmark_summary.json'}")

    # 5. Generate Visualizations
    print("Generating visualizations...")
    
    # Heatmap Data: Aggregate all results to see global skill transfer
    pivot_df = generate_heatmap_data(all_results)
    pivot_df.to_csv(DATA_DIR / "skill_transfer_matrix.csv")
    
    # Leaderboard Data
    leaderboard_df = generate_leaderboard_data(all_results)
    leaderboard_df.to_csv(DATA_DIR / "leaderboard.csv", index=False)
    
    # Plot
    plot_results(pivot_df, leaderboard_df, suffix="all_roles")
    
    print("\nAdaptation Complete.")
    print(f"Artifacts written to: {DATA_DIR}/ and {FIGURES_DIR}/")
    print(f"Key Metric: Best Success Rate = {max(r['Success Rate'] for r in summary_stats):.3f}")

if __name__ == "__main__":
    main()
