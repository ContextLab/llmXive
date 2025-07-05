#!/usr/bin/env python
"""Demonstrate the scoring system for llmXive projects."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from scoring import (
    ScoreTracker, Review,
    ScoreValidator,
    StageManager, ProjectStage
)


def print_score_state(tracker, project_id, stage_manager=None):
    """Print current score state."""
    score = tracker.get_current_score(project_id)
    breakdown = tracker.get_score_breakdown(project_id)
    
    print(f"\n📊 Current Score: {score}")
    print(f"   - Total reviews: {breakdown['total_reviews']}")
    print(f"   - Positive: {breakdown['positive_reviews']} (Human: {breakdown['human_reviews']}, LLM: {breakdown['llm_reviews'] - breakdown['negative_reviews'] - breakdown['critical_reviews']})")
    print(f"   - Negative: {breakdown['negative_reviews']}")
    print(f"   - Critical: {breakdown['critical_reviews']}")
    
    if breakdown['can_advance']:
        print(f"   ✅ Ready to advance!")
    else:
        print(f"   ⏳ Need {breakdown['points_to_advance']:.1f} more points to advance")
    
    if stage_manager:
        stage = stage_manager.get_current_stage(project_id)
        print(f"   🏷️  Current stage: {stage.value}")


def demo_scoring_system():
    """Demonstrate the scoring system."""
    
    print("=== llmXive Scoring System Demo ===\n")
    
    # Initialize components
    tracker = ScoreTracker()
    validator = ScoreValidator(tracker)
    manager = StageManager(tracker)
    project_id = "demo-project"
    
    print("1. Starting a new project in BACKLOG stage")
    print_score_state(tracker, project_id, manager)
    
    # Scenario 1: Building score with mixed reviews
    print("\n2. Adding initial reviews...")
    
    reviews = [
        ("Scenario: Mixed reviews", [
            Review("enthusiastic-llm", is_positive=True, is_human=False, 
                   comment="Great approach! Well structured."),
            Review("supportive-llm", is_positive=True, is_human=False,
                   comment="Good work, minor improvements suggested."),
            Review("critical-llm", is_positive=False, is_human=False,
                   comment="Some concerns about edge cases."),
            Review("human-expert", is_positive=True, is_human=True,
                   comment="Excellent technical foundation!"),
        ])
    ]
    
    for scenario_name, review_list in reviews:
        print(f"\n   {scenario_name}:")
        for review in review_list:
            score = tracker.add_review(project_id, review)
            reviewer_type = "Human" if review.is_human else "LLM"
            impact = review.get_score_impact()
            print(f"   - {reviewer_type} review by {review.reviewer}: "
                  f"{'+' if impact >= 0 else ''}{impact} → Score: {score}")
    
    print_score_state(tracker, project_id, manager)
    
    # Scenario 2: Critical review with stage move
    print("\n3. Critical review scenario (triggers stage move)...")
    
    # First advance to IN_REVIEW stage
    print("   Setting up IN_REVIEW stage for demonstration...")
    manager.set_stage(project_id, ProjectStage.IN_REVIEW, "demo")
    tracker.reset_score(project_id, "stage_change")
    
    # Build up score in IN_REVIEW
    print("   Building up score in IN_REVIEW stage...")
    for i in range(5):
        tracker.add_review(project_id, Review(f"reviewer-{i}", is_positive=True, is_human=False))
    
    print_score_state(tracker, project_id, manager)
    
    print("\n   💥 Critical issue identified in paper review!")
    critical_review = Review("critical-reviewer", is_positive=False, is_critical=True,
                           comment="CRITICAL: Fundamental flaw in methodology!")
    score = tracker.add_review(project_id, critical_review)
    print(f"   Score remains: {score} (stage manager will handle move)")
    
    # Stage manager moves back
    project_state = {'issue_number': 123}
    success, transition = manager.move_to_previous_stage(project_id, project_state, "critical_review")
    if success:
        print(f"   📍 Moved back from {transition.from_stage.value} to {transition.to_stage.value}")
        print(f"   Score reset to: {tracker.get_current_score(project_id)}")
    
    print_score_state(tracker, project_id, manager)
    
    # Scenario 3: Recovery and advancement
    print("\n4. Recovery after addressing critical issue...")
    
    # Add reviews after fixing
    recovery_reviews = [
        Review("original-critic", is_positive=True, is_human=False,
               comment="Edge cases now properly handled."),
        Review("reviewer-1", is_positive=True, is_human=False),
        Review("reviewer-2", is_positive=True, is_human=False),
        Review("reviewer-3", is_positive=True, is_human=False),
        Review("human-reviewer", is_positive=True, is_human=True,
               comment="Comprehensive fix, well done!"),
        Review("reviewer-4", is_positive=True, is_human=False),
        Review("reviewer-5", is_positive=True, is_human=False),
        Review("reviewer-6", is_positive=True, is_human=False),
        Review("reviewer-7", is_positive=True, is_human=False),
    ]
    
    for review in recovery_reviews:
        tracker.add_review(project_id, review)
    
    print_score_state(tracker, project_id, manager)
    
    # Stage advancement
    print("\n5. Stage advancement...")
    
    # Prepare project state for advancement
    project_state = {
        'artifacts': {
            'technical_design_document': 'design.md'
        },
        'has_technical_design': True,
        'issue_number': 123
    }
    
    can_advance, requirements = manager.can_advance(project_id, project_state)
    print(f"\n   Can advance: {can_advance}")
    print("   Requirements check:")
    for req, met in requirements.items():
        status = "✅" if met else "❌"
        print(f"   {status} {req}: {met}")
    
    if can_advance:
        success, transition = manager.advance_stage(project_id, project_state)
        if success:
            print(f"\n   🎉 Advanced from {transition.from_stage.value} to {transition.to_stage.value}!")
            print(f"   Score reset for new stage: {tracker.get_current_score(project_id)}")
    
    # Validation
    print("\n6. Running score validation...")
    
    summary = validator.get_validation_summary(project_id)
    print(summary)
    
    # Score history
    print("\n7. Score history visualization")
    
    history = tracker.get_score_history(project_id)
    print(f"\n   Total events: {len(history)}")
    
    # Show last 5 events
    print("\n   Recent events:")
    for event in history[-5:]:
        timestamp = event['timestamp'].strftime('%H:%M:%S')
        if event['event'] == 'review_added':
            review = event['review']
            print(f"   [{timestamp}] Review by {review.reviewer}: "
                  f"{event['old_score']} → {event['new_score']}")
        else:
            print(f"   [{timestamp}] {event['event']}: "
                  f"{event['old_score']} → {event['new_score']}")
    
    # Stage summary
    print("\n8. Final project summary")
    
    stage_summary = manager.get_stage_summary(project_id, project_state)
    print(f"\n   Project: {project_id}")
    print(f"   Current stage: {stage_summary['current_stage']}")
    print(f"   Next stage: {stage_summary['next_stage']}")
    print(f"   Current score: {stage_summary['current_score']}")
    print(f"   Total transitions: {stage_summary['transition_count']}")
    
    print("\n=== Demo Complete ===")
    print("\nThe updated scoring system provides:")
    print("- Stage progression: Backlog → Ready → In Progress → In Review → Done")
    print("- Score tracking: LLM (±0.5) and Human (±1.0) reviews")
    print("- Negative reviews DO subtract points (floor at 0)")
    print("- Critical reviews trigger move to previous stage (with score reset)")
    print("- Most stages need 5 points to advance")
    print("- In Progress → In Review only needs 1 point (paper completion signal)")
    print("- Complete validation and history tracking")


if __name__ == '__main__':
    demo_scoring_system()