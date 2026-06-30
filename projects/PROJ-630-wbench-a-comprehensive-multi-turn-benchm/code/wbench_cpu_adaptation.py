import os
import sys
import json
import random
import hashlib
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Try to import common libs, fallback to pure python if missing
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    # Fallback simple array implementation if numpy is missing (unlikely in env, but safe)
    class np:
        @staticmethod
        def load(*args, **kwargs): raise NotImplementedError("Numpy required for this fallback")
        @staticmethod
        def array(data): return data
        @staticmethod
        def stack(data): return data
        @staticmethod
        def mean(data, axis=None): return sum(data)/len(data) if not axis else sum(data)/len(data)

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    import matplotlib
    matplotlib.use('Agg') # Force non-interactive backend
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

# Constants
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
WORK_DIR = PROJECT_ROOT / "work_dirs" / "cpu_adaptation"
CASES_DIR = DATA_DIR / "cases"
OUTPUT_DIR = WORK_DIR / "results"
FIGURES_DIR = WORK_DIR / "figures"

# Ensure directories exist
for d in [WORK_DIR, OUTPUT_DIR, FIGURES_DIR, CASES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ============================================================================
# 1. DATA GENERATION (Synthetic Fallback)
# ============================================================================

def generate_synthetic_case(case_id: int) -> Dict[str, Any]:
    """
    Generates a synthetic WBench case structure.
    Simulates: settings, interactions, and metadata.
    """
    perspectives = ["first_person", "third_person"]
    interaction_types = ["navigation", "subject_action", "event_editing", "perspective_switching"]
    nav_actions = ["W", "A", "S", "D", "left", "right", "up", "down"]
    
    # Randomize case properties
    perspective = random.choice(perspectives)
    num_turns = random.randint(3, 8) # Small scale
    interactions = []
    
    for i in range(num_turns):
        # 50% chance of navigation, else other actions
        if random.random() < 0.5:
            action = random.choice(nav_actions)
            inter_type = "navigation"
        else:
            action = random.choice(["look_left", "jump", "change_light", "zoom_in"])
            inter_type = random.choice(["subject_action", "event_editing", "perspective_switching"])
        
        interactions.append({
            "turn": i,
            "action": action,
            "type": inter_type,
            "description": f"Turn {i} action: {action}",
            "duration": round(random.uniform(1.0, 3.0), 2)
        })
    
    case = {
        "id": case_id,
        "settings": {
            "perspective": perspective,
            "scene": "urban_street" if random.random() > 0.5 else "indoor_room",
            "style": "realistic"
        },
        "interactions": interactions,
        "metadata": {
            "source": "synthetic_generator",
            "original_video_path": None
        }
    }
    return case

def load_or_generate_cases(target_count: int = 10) -> List[Dict[str, Any]]:
    """
    Tries to load real cases from data/cases. If none found or too few,
    generates synthetic ones to reach target_count.
    """
    cases = []
    
    # Try to find real cases
    if CASES_DIR.exists():
        json_files = list(CASES_DIR.glob("case_*.json"))
        for f in json_files:
            try:
                with open(f, 'r') as fh:
                    cases.append(json.load(fh))
                if len(cases) >= target_count:
                    break
            except Exception:
                continue
    
    # Generate synthetic if needed
    start_id = len(cases) + 1
    while len(cases) < target_count:
        case = generate_synthetic_case(start_id)
        cases.append(case)
        # Save synthetic case for future runs
        save_path = CASES_DIR / f"case_{start_id}.json"
        with open(save_path, 'w') as fh:
            json.dump(case, fh, indent=2)
        start_id += 1
        
    return cases[:target_count]

# ============================================================================
# 2. METRIC SIMULATION (CPU Tractable Proxies)
# ============================================================================

def compute_video_quality_proxy(case: Dict) -> float:
    """
    Simulates video quality metrics (Aesthetic, Imaging, Motion)
    using random noise + case metadata as a proxy.
    In real WBench, this uses heavy vision models (HPSv3, etc.).
    """
    # Deterministic seed based on case ID for reproducibility
    seed = int(str(case["id"]) + "01")
    rng = random.Random(seed)
    
    # Simulate scores between 0 and 10
    aesthetic = 6.0 + rng.gauss(0, 1.5)
    imaging = 5.5 + rng.gauss(0, 1.2)
    motion = 4.0 + rng.gauss(0, 1.0)
    
    # Clamp
    aesthetic = max(0, min(10, aesthetic))
    imaging = max(0, min(10, imaging))
    motion = max(0, min(10, motion))
    
    return {
        "aesthetic_score": round(aesthetic, 3),
        "imaging_score": round(imaging, 3),
        "motion_score": round(motion, 3),
        "composite_quality": round((aesthetic + imaging + motion) / 3, 3)
    }

def compute_consistency_proxy(case: Dict) -> Dict[str, float]:
    """
    Simulates consistency metrics (Background, Subject, Perspective).
    Real WBench uses SAM2 masks and depth estimation.
    """
    seed = int(str(case["id"]) + "02")
    rng = random.Random(seed)
    
    # Navigation cases tend to have lower consistency in this simulation
    is_navi = any(t["type"] == "navigation" for t in case["interactions"])
    penalty = 1.5 if is_navi else 0
    
    bg_score = 8.0 + rng.gauss(0, 1.0) - penalty
    subj_score = 7.5 + rng.gauss(0, 1.2) - penalty
    persp_score = 7.0 + rng.gauss(0, 1.5) if case["settings"]["perspective"] == "first_person" else 6.5
    
    return {
        "background_consistency": round(max(0, min(10, bg_score)), 3),
        "subject_consistency": round(max(0, min(10, subj_score)), 3),
        "perspective_consistency": round(max(0, min(10, persp_score)), 3)
    }

def compute_navigation_proxy(case: Dict) -> Dict[str, Any]:
    """
    Simulates navigation trajectory adherence.
    Real WBench compares generated camera poses (MegaSAM) to ground truth.
    """
    seed = int(str(case["id"]) + "03")
    rng = random.Random(seed)
    
    nav_turns = [t for t in case["interactions"] if t["type"] == "navigation"]
    if not nav_turns:
        return {"nav_score": None, "error": "No navigation turns"}
    
    # Simulate adherence score
    adherence = 7.0 + rng.gauss(0, 1.5)
    adherence = max(0, min(10, adherence))
    
    return {
        "nav_score": round(adherence, 3),
        "num_nav_turns": len(nav_turns),
        "perspective": case["settings"]["perspective"]
    }

def compute_physics_proxy(case: Dict) -> Dict[str, float]:
    """
    Simulates physics compliance (Causal Fidelity, Visual Plausibility).
    """
    seed = int(str(case["id"]) + "04")
    rng = random.Random(seed)
    
    causal = 6.5 + rng.gauss(0, 1.8)
    plausibility = 7.0 + rng.gauss(0, 1.5)
    
    return {
        "causal_fidelity": round(max(0, min(10, causal)), 3),
        "visual_plausibility": round(max(0, min(10, plausibility)), 3)
    }

# ============================================================================
# 3. MAIN EVALUATION PIPELINE
# ============================================================================

def run_evaluation(cases: List[Dict]) -> List[Dict]:
    """
    Runs all proxy metrics for a list of cases.
    """
    results = []
    
    print(f"\n{'='*60}")
    print(f"  Starting CPU-Safe WBench Adaptation Evaluation")
    print(f"  Cases to process: {len(cases)}")
    print(f"{'='*60}\n")
    
    for i, case in enumerate(cases):
        cid = case["id"]
        print(f"[{i+1}/{len(cases)}] Processing case_{cid}...")
        
        try:
            # 1. Video Quality
            vq = compute_video_quality_proxy(case)
            
            # 2. Consistency
            cons = compute_consistency_proxy(case)
            
            # 3. Navigation
            nav = compute_navigation_proxy(case)
            
            # 4. Physics
            phys = compute_physics_proxy(case)
            
            # Aggregate
            scores = {
                "video_quality": vq,
                "consistency": cons,
                "navigation": nav,
                "physics": phys
            }
            
            # Calculate a simple "Total Score" (average of non-null metrics)
            all_scores = []
            all_scores.append(vq["composite_quality"])
            all_scores.append(cons["background_consistency"])
            all_scores.append(cons["subject_consistency"])
            all_scores.append(cons["perspective_consistency"])
            if nav["nav_score"] is not None:
                all_scores.append(nav["nav_score"])
            all_scores.append(phys["causal_fidelity"])
            all_scores.append(phys["visual_plausibility"])
            
            total_score = round(sum(all_scores) / len(all_scores), 3)
            
            result = {
                "case_id": cid,
                "perspective": case["settings"]["perspective"],
                "num_turns": len(case["interactions"]),
                "is_navigation": any(t["type"] == "navigation" for t in case["interactions"]),
                "scores": scores,
                "total_score": total_score
            }
            results.append(result)
            print(f"  -> Total Score: {total_score}")
            
        except Exception as e:
            print(f"  -> ERROR: {e}")
            results.append({
                "case_id": cid,
                "error": str(e),
                "total_score": None
            })
            
    return results

def generate_plots(results: List[Dict]):
    """
    Generates summary plots if matplotlib is available.
    """
    if not HAS_MATPLOTLIB:
        print("Matplotlib not found. Skipping plots.")
        return

    # Filter out errors
    valid_results = [r for r in results if r.get("total_score") is not None]
    if not valid_results:
        print("No valid results to plot.")
        return

    # Plot 1: Score Distribution
    scores = [r["total_score"] for r in valid_results]
    
    plt.figure(figsize=(10, 6))
    plt.hist(scores, bins=10, color='skyblue', edgecolor='black', alpha=0.7)
    plt.axvline(np.mean(scores), color='red', linestyle='--', label=f'Mean: {np.mean(scores):.2f}')
    plt.title("WBench CPU Adaptation: Total Score Distribution")
    plt.xlabel("Total Score")
    plt.ylabel("Frequency")
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    
    plt.savefig(FIGURES_DIR / "score_distribution.png", dpi=100, bbox_inches='tight')
    plt.close()
    print(f"  Saved plot: score_distribution.png")

    # Plot 2: Navigation vs Non-Navigation Performance
    nav_scores = [r["total_score"] for r in valid_results if r.get("is_navigation")]
    non_nav_scores = [r["total_score"] for r in valid_results if not r.get("is_navigation")]
    
    plt.figure(figsize=(8, 6))
    box_data = [nav_scores, non_nav_scores]
    labels = ["Navigation Cases", "Non-Navigation Cases"]
    
    bp = plt.boxplot(box_data, labels=labels, patch_artist=True,
                     boxprops=dict(facecolor='#ADD8E6'),
                     medianprops=dict(color='red'))
    
    plt.title("Performance: Navigation vs Non-Navigation")
    plt.ylabel("Total Score")
    plt.grid(axis='y', alpha=0.3)
    
    plt.savefig(FIGURES_DIR / "nav_vs_nonnav.png", dpi=100, bbox_inches='tight')
    plt.close()
    print(f"  Saved plot: nav_vs_nonnav.png")

def save_results(results: List[Dict], cases: List[Dict]):
    """
    Saves results to CSV and JSON.
    """
    # CSV
    if HAS_PANDAS:
        df = pd.DataFrame(results)
        # Flatten scores for CSV
        csv_data = []
        for r in results:
            row = {
                "case_id": r["case_id"],
                "perspective": r["perspective"],
                "num_turns": r["num_turns"],
                "is_navigation": r["is_navigation"],
                "total_score": r["total_score"]
            }
            # Flatten nested scores
            if "scores" in r:
                for cat, metrics in r["scores"].items():
                    if isinstance(metrics, dict):
                        for k, v in metrics.items():
                            row[f"{cat}_{k}"] = v
            csv_data.append(row)
        
        df_flat = pd.DataFrame(csv_data)
        df_flat.to_csv(OUTPUT_DIR / "results.csv", index=False)
    else:
        # Fallback manual CSV writing
        with open(OUTPUT_DIR / "results.csv", 'w') as f:
            f.write("case_id,perspective,num_turns,is_navigation,total_score\n")
            for r in results:
                f.write(f"{r['case_id']},{r['perspective']},{r['num_turns']},{r['is_navigation']},{r['total_score']}\n")
    
    # JSON (Full detail)
    with open(OUTPUT_DIR / "results_full.json", 'w') as f:
        json.dump(results, f, indent=2)
        
    # Summary JSON (Aggregated)
    valid_scores = [r["total_score"] for r in results if r.get("total_score") is not None]
    summary = {
        "total_cases": len(results),
        "processed_cases": len(valid_scores),
        "average_score": round(sum(valid_scores)/len(valid_scores), 3) if valid_scores else 0,
        "min_score": min(valid_scores) if valid_scores else 0,
        "max_score": max(valid_scores) if valid_scores else 0,
        "note": "CPU Adaptation: Synthetic/Scaled Proxy Metrics"
    }
    with open(OUTPUT_DIR / "summary.json", 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"  Saved results.csv, results_full.json, summary.json")

# ============================================================================
# MAIN ENTRY
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="WBench CPU Adaptation Runner")
    parser.add_argument("--cases", type=int, default=10, help="Number of cases to process (synthetic if missing)")
    parser.add_argument("--regenerate", action="store_true", help="Force regeneration of synthetic cases")
    args = parser.parse_args()

    print("WBench CPU Adaptation Starting...")
    print(f"Environment: CPU Only, No GPU, < 25 mins budget")
    
    # 1. Load/Generate Cases
    if args.regenerate:
        import shutil
        if CASES_DIR.exists():
            shutil.rmtree(CASES_DIR)
        CASES_DIR.mkdir(parents=True, exist_ok=True)
    
    cases = load_or_generate_cases(target_count=args.cases)
    print(f"Loaded/Generated {len(cases)} cases.")

    # 2. Run Evaluation
    results = run_evaluation(cases)

    # 3. Generate Artifacts
    generate_plots(results)
    save_results(results, cases)

    print(f"\n{'='*60}")
    print(f"  Evaluation Complete!")
    print(f"  Outputs saved to: {OUTPUT_DIR}")
    print(f"  Figures saved to: {FIGURES_DIR}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
