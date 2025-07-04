#!/usr/bin/env python3
"""Fix project board status for issues showing 'No Status'"""

import os
import json
import subprocess


def get_issues_without_status():
    """Get all issues that have no status in the project board"""
    cmd = ['gh', 'project', 'item-list', '13', '--owner', 'ContextLab', '--format', 'json']
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error getting project items: {result.stderr}")
        return []
    
    data = json.loads(result.stdout)
    items_without_status = []
    
    for item in data.get('items', []):
        # Check if status is null, empty, or "No Status"
        status = item.get('status')
        if status is None or status == '' or status == 'No Status':
            items_without_status.append({
                'id': item['id'],
                'issue_number': item.get('content', {}).get('number'),
                'title': item.get('content', {}).get('title', 'Unknown')[:60] + '...'
            })
    
    return items_without_status


def update_item_status(item_id, status_option_id='f75ad846'):
    """Update a project item's status to Backlog (or specified status)"""
    cmd = [
        'gh', 'project', 'item-edit',
        '--id', item_id,
        '--field-id', 'PVTSSF_lADOAVVqQM4A9CYqzgw2-6c',  # Status field ID
        '--project-id', 'PVT_kwDOAVVqQM4A9CYq',
        '--single-select-option-id', status_option_id  # Backlog by default
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def main():
    """Main function to fix all project board statuses"""
    print("Fixing project board statuses...")
    print("=" * 60)
    
    # Get issues without status
    items = get_issues_without_status()
    
    if not items:
        print("No items found with missing status!")
        return
    
    print(f"Found {len(items)} items with no status:")
    for item in items:
        print(f"  - Issue #{item['issue_number']}: {item['title']}")
    
    print("\nUpdating statuses to 'Backlog'...")
    print("-" * 60)
    
    success_count = 0
    for item in items:
        print(f"\nUpdating issue #{item['issue_number']}...")
        if update_item_status(item['id']):
            print(f"  ✓ Successfully set to Backlog")
            success_count += 1
        else:
            print(f"  ✗ Failed to update status")
    
    print("\n" + "=" * 60)
    print(f"Summary: Updated {success_count}/{len(items)} items")
    
    # Also ensure any issues not in the project are added
    print("\nChecking for issues not in project board...")
    check_and_add_missing_issues()


def check_and_add_missing_issues():
    """Check for idea issues that aren't in the project board and add them"""
    # Get all idea issues from the repository
    cmd = ['gh', 'issue', 'list', '--repo', 'ContextLab/llmXive', '--label', 'backlog', '--json', 'number,title', '--limit', '100']
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error getting issues: {result.stderr}")
        return
    
    all_issues = json.loads(result.stdout)
    
    # Get issues already in project
    cmd = ['gh', 'project', 'item-list', '13', '--owner', 'ContextLab', '--format', 'json']
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        return
    
    project_data = json.loads(result.stdout)
    project_issue_numbers = set()
    
    for item in project_data.get('items', []):
        content = item.get('content', {})
        if content.get('number'):
            project_issue_numbers.add(content['number'])
    
    # Find issues not in project
    missing_issues = []
    for issue in all_issues:
        if issue['number'] not in project_issue_numbers:
            missing_issues.append(issue)
    
    if missing_issues:
        print(f"\nFound {len(missing_issues)} issues not in project:")
        for issue in missing_issues:
            print(f"  - Issue #{issue['number']}: {issue['title'][:60]}...")
            
            # Add to project
            cmd = [
                'gh', 'project', 'item-add', '13',
                '--owner', 'ContextLab',
                '--url', f"https://github.com/ContextLab/llmXive/issues/{issue['number']}"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"    ✓ Added to project board")
                
                # Now set its status to Backlog
                # Get the new item ID
                cmd = ['gh', 'project', 'item-list', '13', '--owner', 'ContextLab', '--format', 'json']
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    for item in data.get('items', []):
                        if item.get('content', {}).get('number') == issue['number']:
                            if update_item_status(item['id']):
                                print(f"    ✓ Set status to Backlog")
                            break
            else:
                print(f"    ✗ Failed to add to project")
    else:
        print("\nAll backlog issues are already in the project board!")


if __name__ == "__main__":
    main()