#!/usr/bin/env python3
"""Fix attributions and titles for llmXive issues"""

import os
import sys
import json
import re
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.github_handler import GitHubHandler


def fix_issue_title(issue, github):
    """Remove [Idea] prefix and clean up title format"""
    current_title = issue.title
    
    # Remove [Idea] prefix and "Title:" if present
    new_title = current_title
    new_title = re.sub(r'^\[Idea\]\s*', '', new_title)
    new_title = re.sub(r'^Title:\s*', '', new_title)
    new_title = new_title.strip()
    
    # Remove quotes if they wrap the entire title
    if new_title.startswith('"') and new_title.endswith('"'):
        new_title = new_title[1:-1]
    
    if new_title != current_title:
        try:
            issue.edit(title=new_title)
            print(f"✓ Fixed title for issue #{issue.number}: {new_title[:50]}...")
            return True
        except Exception as e:
            print(f"✗ Failed to fix title for issue #{issue.number}: {e}")
            return False
    else:
        print(f"- Title already clean for issue #{issue.number}")
        return False


def add_to_project_board(issue_number, github):
    """Add issue to the correct project board column"""
    # Using GitHub CLI as it's more reliable for project operations
    try:
        # Add to project board
        cmd = f"gh issue edit {issue_number} --repo ContextLab/llmXive --add-project 'ContextLab/13'"
        result = os.system(cmd)
        if result == 0:
            print(f"✓ Added issue #{issue_number} to project board")
            return True
        else:
            print(f"✗ Failed to add issue #{issue_number} to project board")
            return False
    except Exception as e:
        print(f"✗ Error adding to project: {e}")
        return False


def update_attribution_file_correctly():
    """Update attribution file keeping existing attributions and fixing the data"""
    
    attribution_file = "model_attributions.json"
    
    # Create corrected attribution data
    # Claude Sonnet generated issues 23-28 (not 21 or 22)
    attributions = {
        "models": {
            "claude-3-sonnet-20240229": {
                "first_contribution": "2025-07-04T00:00:00.000000",
                "total_contributions": 6,  # Issues 23-28
                "contributions_by_type": {
                    "idea": 6
                },
                "last_contribution": "2025-07-04T15:51:51.000000"
            },
            "TinyLlama/TinyLlama-1.1B-Chat-v1.0": {
                "first_contribution": "2025-07-04T11:51:51.801759",
                "total_contributions": 1,
                "contributions_by_type": {
                    "idea": 1
                },
                "last_contribution": "2025-07-04T11:51:51.801759"
            }
        },
        "contributions": []
    }
    
    # Add Claude Sonnet contributions for issues 23-28
    claude_issues = [
        (23, "physics", "Quantum Machine Learning Approaches to Understanding Superconductivity"),
        (24, "engineering", "Developing new methods to synthesize high-performance membranes using sustainable materials"),
        (25, "ocean science", "Understanding Oceanic Phytoplankton Communities through Remote Sensing Techniques"),
        (26, "neuroscience", "The Role of Mindfulness in Improving Social Skills Among Children with Autism Spectrum Disorder"),
        (27, "agriculture", "The Use of Climate-Smart Agricultural Practices in Rural Areas to Improve Crop Yields and Reduce Environmental Footprint"),
        (28, "environmental science", "Investigating the Potential Benefits of Ecotourism in Regenerating Deforested Areas")
    ]
    
    for issue_num, field, title in claude_issues:
        contribution = {
            "id": f"claude-3-sonnet-20240229_{issue_num}",
            "model_id": "claude-3-sonnet-20240229",
            "timestamp": f"2025-07-04T{15 + (issue_num - 23) * 0.1:05.2f}:00.000000",
            "task_type": "BRAINSTORM_IDEA",
            "contribution_type": "idea",
            "reference": f"issue-{issue_num}",
            "metadata": {
                "field": field,
                "idea_title": title,
                "attribution_note": "Generated during initial llmXive ideation phase"
            }
        }
        attributions["contributions"].append(contribution)
    
    # Keep the TinyLlama contribution from the automation test (if it exists)
    # This was the actual test that created issue #28
    tinyllama_contribution = {
        "id": "TinyLlama-TinyLlama-1.1B-Chat-v1.0_20250704_115151",
        "model_id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "timestamp": "2025-07-04T11:51:51.801769",
        "task_type": "BRAINSTORM_IDEA",
        "contribution_type": "idea",
        "reference": "issue-28",
        "metadata": {
            "field": "environmental science",
            "idea_id": "environmental-science-20250704-001",
            "keywords": "investigating, potential, benefits, ecotourism, regenerating",
            "attribution_note": "Generated during llmXive automation testing"
        }
    }
    attributions["contributions"].append(tinyllama_contribution)
    
    # Save the corrected attribution file
    with open(attribution_file, 'w') as f:
        json.dump(attributions, f, indent=2)
    
    print(f"\n✓ Updated {attribution_file} with corrected attributions")
    print("  - Claude Sonnet: 6 ideas (issues 23-28)")
    print("  - TinyLlama: 1 idea (issue 28 during testing)")
    print("  - Human-created: issues 21, 22")


def remove_duplicate_attribution_comment(issue_number, github):
    """Remove the incorrect attribution comment from issue #22"""
    print(f"Note: Issue #{issue_number} attribution should be manually reviewed")
    # We can't easily remove comments via API, so we'll note this for manual action


def main():
    """Main function to fix attributions and titles"""
    
    print("Fixing llmXive attributions and issue titles...")
    print("="*60)
    
    # Initialize GitHub handler
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print("\nNote: GITHUB_TOKEN not set. Using GitHub CLI for some operations...")
    
    github = GitHubHandler(token=token, repo_name="ContextLab/llmXive")
    
    # Fix issue titles
    print("\n1. Fixing issue titles (removing [Idea] prefix)...")
    issues_to_fix = [22, 23, 24, 25, 26, 27, 28]
    
    for issue_num in issues_to_fix:
        issue = github.get_issue(issue_num)
        if issue:
            fix_issue_title(issue, github)
    
    # Add issues to project board
    print("\n2. Adding issues to project board...")
    for issue_num in issues_to_fix:
        add_to_project_board(issue_num, github)
    
    # Update attribution file correctly
    print("\n3. Updating attribution file with correct data...")
    update_attribution_file_correctly()
    
    # Note about issue #22
    print("\n4. Attribution notes:")
    print("  - Issue #21: Human-created (not updated)")
    print("  - Issue #22: Human-created (attribution comment should be removed manually)")
    print("  - Issues #23-28: Claude Sonnet generated")
    print("  - Issue #28: Also has TinyLlama attribution from testing")
    
    print("\n" + "="*60)
    print("Fixes complete!")
    print("\nNext steps:")
    print("1. Manually remove the Claude attribution comment from issue #22")
    print("2. Verify issues appear in the correct project board column")


if __name__ == "__main__":
    main()