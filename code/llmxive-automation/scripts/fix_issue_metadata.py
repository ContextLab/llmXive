#!/usr/bin/env python3
"""Fix issue metadata - add scores, keywords, and sync with project board"""

import os
import sys
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.github_handler import GitHubHandler
from src.response_parser import ResponseParser


def extract_keywords_from_title(title):
    """Extract keywords from issue title"""
    # Remove common words and extract meaningful keywords
    stop_words = {'the', 'of', 'in', 'to', 'for', 'and', 'a', 'an', 'with', 'using', 'through', 'on'}
    
    # Convert to lowercase and split
    words = title.lower().split()
    
    # Filter out stop words and short words
    keywords = []
    for word in words:
        word = word.strip('.,!?";')
        if len(word) > 3 and word not in stop_words:
            keywords.append(word)
    
    # Take first 5 keywords
    return keywords[:5]


def add_keywords_to_issue(issue, github):
    """Add keyword labels to an issue"""
    # Extract keywords from title
    keywords = extract_keywords_from_title(issue.title)
    
    # Get current labels
    current_labels = [label.name for label in issue.labels]
    
    # Add keyword labels (skip if they already exist)
    added_keywords = []
    for keyword in keywords:
        if keyword not in current_labels:
            try:
                # Create label if it doesn't exist
                github.repo.create_label(keyword, "FFFF00")  # Yellow for keywords
            except:
                pass  # Label might already exist
            added_keywords.append(keyword)
    
    if added_keywords:
        # Update issue labels
        all_labels = current_labels + added_keywords
        issue.set_labels(*all_labels)
        print(f"  Added keywords to issue #{issue.number}: {', '.join(added_keywords)}")
    else:
        print(f"  Issue #{issue.number} already has keywords")
    
    return added_keywords


def ensure_score_label(issue, github):
    """Ensure issue has a score label"""
    current_labels = [label.name for label in issue.labels]
    
    # Check if issue already has a score
    has_score = any(label.startswith("Score:") for label in current_labels)
    
    if not has_score:
        # Add Score: 0 label
        try:
            github.repo.create_label("Score: 0", "0066CC")  # Blue for scores
        except:
            pass  # Label might already exist
        
        current_labels.append("Score: 0")
        issue.set_labels(*current_labels)
        print(f"  Added Score: 0 to issue #{issue.number}")
        return True
    else:
        print(f"  Issue #{issue.number} already has score")
        return False


def sync_with_project_board(issue_number):
    """Sync issue with project board status"""
    # Use GitHub CLI to update project board status
    try:
        # Get the item ID for this issue in the project
        result = os.popen(f'gh project item-list 13 --owner ContextLab --format json | jq -r \'.items[] | select(.content.number == {issue_number}) | .id\'').read().strip()
        
        if result:
            # Set status to Backlog
            cmd = f'gh project item-edit --id "{result}" --field-id PVTSSF_lADOAVVqQM4A9CYqzgw2-6c --project-id PVT_kwDOAVVqQM4A9CYq --single-select-option-id f75ad846'
            status = os.system(cmd)
            if status == 0:
                print(f"  ✓ Set issue #{issue_number} to Backlog in project board")
                return True
            else:
                print(f"  ✗ Failed to update project board for issue #{issue_number}")
                return False
        else:
            # Issue not in project, add it
            cmd = f'gh project item-add 13 --owner ContextLab --url "https://github.com/ContextLab/llmXive/issues/{issue_number}"'
            status = os.system(cmd)
            if status == 0:
                print(f"  ✓ Added issue #{issue_number} to project board")
                # Now set status
                return sync_with_project_board(issue_number)
            else:
                print(f"  ✗ Failed to add issue #{issue_number} to project")
                return False
    except Exception as e:
        print(f"  ✗ Error syncing issue #{issue_number}: {e}")
        return False


def main():
    """Main function to fix issue metadata"""
    
    print("Fixing issue metadata (scores, keywords, project board sync)...")
    print("="*60)
    
    # Initialize GitHub handler
    token = os.environ.get('GITHUB_TOKEN')
    github = GitHubHandler(token=token, repo_name="ContextLab/llmXive")
    
    # Issues to fix
    issue_numbers = [22, 23, 24, 25, 26, 27, 28]
    
    for issue_num in issue_numbers:
        print(f"\nProcessing issue #{issue_num}...")
        
        # Get the issue
        issue = github.get_issue(issue_num)
        if not issue:
            print(f"  ✗ Could not fetch issue #{issue_num}")
            continue
        
        print(f"  Title: {issue.title[:60]}...")
        
        # 1. Add keywords
        add_keywords_to_issue(issue, github)
        
        # 2. Ensure score label
        ensure_score_label(issue, github)
        
        # 3. Sync with project board
        sync_with_project_board(issue_num)
    
    print("\n" + "="*60)
    print("Metadata fixes complete!")
    
    # Also update the task executor to ensure it adds issues to project board
    print("\nNote: The automation system already adds 'Score: 0' label to new issues.")
    print("To ensure new issues are added to the project board, the system should")
    print("use the GitHub CLI to add them after creation.")


if __name__ == "__main__":
    main()