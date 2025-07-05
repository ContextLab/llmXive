#!/usr/bin/env python3
"""Visualize the pipeline test results."""

import json
from pathlib import Path
from collections import defaultdict

def load_test_results():
    """Load the test results from the JSON file."""
    results_path = Path("test_output/full_pipeline_test/test_report.json")
    with open(results_path) as f:
        return json.load(f)

def print_stage_progression(history):
    """Print the stage progression through the test."""
    print("\n🚀 STAGE PROGRESSION")
    print("=" * 60)
    
    stage_transitions = []
    current_stage = None
    
    for event in history:
        if event['stage'] != current_stage:
            current_stage = event['stage']
            stage_transitions.append({
                'step': event['step'],
                'stage': current_stage,
                'score': event['score']
            })
    
    for i, transition in enumerate(stage_transitions):
        arrow = " → " if i > 0 else ""
        print(f"{arrow}Step {transition['step']}: {transition['stage'].upper()} (score: {transition['score']})")

def print_artifact_summary(artifacts):
    """Print summary of created artifacts."""
    print("\n📦 ARTIFACTS CREATED")
    print("=" * 60)
    
    artifact_types = defaultdict(list)
    for name, path in artifacts.items():
        # Group by type
        if 'technical_design' in name:
            artifact_types['Technical Design'].append(path)
        elif 'implementation_plan' in name:
            artifact_types['Implementation Plan'].append(path)
        elif 'code' in name or 'tests' in name:
            artifact_types['Code & Tests'].append(path)
        elif 'data' in name or 'analysis' in name:
            artifact_types['Data & Analysis'].append(path)
        elif 'paper' in name or 'pdf' in name or 'figures' in name:
            artifact_types['Paper & Figures'].append(path)
        elif 'readme' in name:
            artifact_types['Documentation'].append(path)
    
    for category, paths in artifact_types.items():
        print(f"\n{category}:")
        for path in paths:
            print(f"  ✓ {path}")

def print_review_summary(history):
    """Print summary of reviews."""
    print("\n👥 REVIEW SUMMARY")
    print("=" * 60)
    
    reviews_by_stage = defaultdict(lambda: {'positive': 0, 'negative': 0, 'critical': 0})
    
    for event in history:
        if event['type'] == 'review':
            stage = event['stage']
            if 'response_type' in event:
                if event['response_type'] == 'positive':
                    reviews_by_stage[stage]['positive'] += event.get('review_count', 1)
                elif event['response_type'] == 'negative':
                    reviews_by_stage[stage]['negative'] += event.get('review_count', 1)
                elif event['response_type'] == 'critical':
                    reviews_by_stage[stage]['critical'] += event.get('review_count', 1)
    
    for stage, counts in reviews_by_stage.items():
        print(f"\n{stage.upper()}:")
        print(f"  ✅ Positive: {counts['positive']}")
        print(f"  ❌ Negative: {counts['negative']}")
        print(f"  🚨 Critical: {counts['critical']}")

def print_score_progression(history):
    """Print score progression through the test."""
    print("\n📊 SCORE PROGRESSION")
    print("=" * 60)
    
    score_changes = []
    for i, event in enumerate(history):
        if i == 0 or event['score'] != history[i-1]['score']:
            score_changes.append({
                'step': event['step'],
                'score': event['score'],
                'action': event['description'],
                'stage': event['stage']
            })
    
    for change in score_changes:
        print(f"Step {change['step']:2d}: {change['score']:4.1f} - {change['action']} [{change['stage']}]")

def print_key_milestones(history):
    """Print key milestones in the test."""
    print("\n🎯 KEY MILESTONES")
    print("=" * 60)
    
    milestones = [
        "Create technical design document",
        "Critical design review",
        "Advance to Ready stage",
        "Create implementation plan",
        "Advance to In Progress",
        "Generate initial code",
        "Write Abstract",
        "Final paper reviews (10 positive)",
        "Move to Done"
    ]
    
    for event in history:
        if event['description'] in milestones:
            status = "✓" if event['type'] != 'advance_stage' or event['stage'] != 'in_review' else "⚠️"
            print(f"{status} Step {event['step']:2d}: {event['description']}")

def main():
    """Main function."""
    data = load_test_results()
    
    print("\n" + "=" * 80)
    print("🧪 LLMXIVE PIPELINE TEST RESULTS VISUALIZATION")
    print("=" * 80)
    
    # Overall summary
    result = data['test_result']
    print(f"\nOverall Status: {'✅ PASSED' if result['success'] else '❌ FAILED'}")
    print(f"Steps Completed: {result['completed_steps']}/{result['total_steps']}")
    print(f"Duration: {result['duration_seconds']:.3f} seconds")
    print(f"Validation Pass Rate: {result['validation_summary']['pass_rate']:.1f}%")
    
    # Stage progression
    print_stage_progression(data['history'])
    
    # Key milestones
    print_key_milestones(data['history'])
    
    # Score progression
    print_score_progression(data['history'])
    
    # Review summary
    print_review_summary(data['history'])
    
    # Artifacts
    print_artifact_summary(data['final_state']['artifacts'])
    
    # Final state
    print("\n🏁 FINAL STATE")
    print("=" * 60)
    print(f"Project: {data['final_state']['project_id']}")
    print(f"Stage: {data['final_state']['stage'].upper()}")
    print(f"Score: {data['final_state']['score']}")
    print(f"Total Artifacts: {len(data['final_state']['artifacts'])}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()