# GitHub Repository Roles Setup

## Overview

llmXive uses GitHub's custom repository roles feature to manage user permissions. This allows fine-grained control over who can modify AI models, approve reviews, and perform administrative tasks.

## Setting Up Custom Roles

### 1. Access Repository Settings

Go to: https://github.com/ContextLab/llmXive/settings/access

### 2. Create Custom Roles

Create the following custom roles with their respective permissions:

#### **llmxive-admin** (Full Administrator)
- **Description**: Full system administrator with model modification rights
- **Base Role**: Admin
- **Additional Permissions**:
  - Manage repository settings
  - Manage collaborators
  - Create/modify/delete AI models
  - Assign user roles
  - Configure system settings

#### **llmxive-moderator** (Content Moderator)  
- **Description**: Content and review moderator
- **Base Role**: Write
- **Permissions**:
  - Moderate content and reviews
  - Approve/reject submissions
  - Manage user reports
  - View all content

#### **llmxive-reviewer** (Trusted Reviewer)
- **Description**: Trusted reviewer with approval permissions
- **Base Role**: Triage
- **Permissions**:
  - Approve reviews and research artifacts
  - Create and update projects
  - Submit ideas and vote

#### **llmxive-contributor** (Default User)
- **Description**: Default authenticated user role
- **Base Role**: Read
- **Permissions**:
  - Submit reviews and ideas
  - Vote on research artifacts
  - Create projects
  - View all public content

#### **llmxive-viewer** (Read-Only)
- **Description**: Read-only access
- **Base Role**: Read
- **Permissions**:
  - View public content only
  - No modification rights

## Role Assignment Process

### 1. Automatic Assignment

When users authenticate, their role is determined by:

1. **Repository Owner**: Automatically gets `admin` role
2. **Custom Role**: If assigned in GitHub settings, maps to corresponding llmXive role
3. **Standard Collaborator**: Maps based on GitHub permission level
4. **Default**: Authenticated users get `contributor` role

### 2. Role Mapping

```javascript
// GitHub Custom Role → llmXive Role
'llmxive-admin' → 'admin'
'llmxive-moderator' → 'moderator' 
'llmxive-reviewer' → 'reviewer'
'llmxive-contributor' → 'contributor'
'llmxive-viewer' → 'viewer'

// GitHub Standard Permission → llmXive Role
'admin' → 'moderator'     // GitHub admin becomes llmXive moderator
'maintain' → 'moderator'
'write' → 'contributor'
'triage' → 'contributor'  
'read' → 'viewer'
```

### 3. Default Permissions

**Unauthenticated users** get `anonymous` role with minimal permissions.

**Authenticated users without specific roles** get `contributor` role, allowing them to:
- ✅ Submit reviews and ideas
- ✅ Vote on research artifacts  
- ✅ Create projects
- ✅ View all content
- ❌ Cannot modify AI models
- ❌ Cannot approve reviews
- ❌ Cannot change system settings

## Permission Matrix

| Action | Anonymous | Viewer | Contributor | Reviewer | Moderator | Admin |
|--------|-----------|--------|-------------|----------|-----------|-------|
| **View Content** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Submit Ideas** | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Submit Reviews** | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Vote on Artifacts** | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Create Projects** | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Approve Reviews** | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| **Moderate Content** | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Modify AI Models** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Assign Roles** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **System Config** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

## Assigning Users to Roles

### Method 1: Repository Settings (Recommended)

1. Go to https://github.com/ContextLab/llmXive/settings/access
2. Click "Invite a collaborator"
3. Enter user's GitHub username
4. Select the appropriate custom role (e.g., `llmxive-reviewer`)
5. Send invitation

### Method 2: Direct Collaborator Assignment

1. Go to repository Settings > Collaborators
2. Add user with standard GitHub permission
3. System will map to appropriate llmXive role automatically

### Method 3: Bulk Assignment (For Organizations)

If ContextLab is a GitHub Organization:
1. Create teams for each role level
2. Assign custom roles to teams
3. Add users to appropriate teams

## Example User Scenarios

### Research Scientist
```
Role: llmxive-reviewer
Permissions: Can approve reviews, submit ideas, vote
Cannot: Modify AI models, change system settings
```

### Lab Administrator  
```
Role: llmxive-admin
Permissions: Full access including model modification
Can: Add/remove models, assign roles, configure system
```

### Graduate Student
```
Role: llmxive-contributor (default)
Permissions: Submit reviews and ideas, vote, create projects
Cannot: Approve reviews, modify models
```

### External Collaborator
```
Role: llmxive-viewer
Permissions: Read-only access to public content
Cannot: Submit content, vote, or modify anything
```

## Implementation Details

### Custom Role Detection

The system checks for custom roles using GitHub's API:

```javascript
// Check for custom repository role
const response = await github.request('GET /repos/{owner}/{repo}/collaborators/{username}');
const customRole = response.data.role_name; // e.g., 'llmxive-admin'
```

### Fallback Behavior

If a user doesn't have a custom role:
1. Check standard GitHub collaborator permission
2. Map to equivalent llmXive role
3. Default to `contributor` for authenticated users
4. Default to `anonymous` for unauthenticated users

### Role Inheritance

Roles inherit permissions from lower levels:
- `admin` has all permissions from `moderator`, `reviewer`, `contributor`, `viewer`
- `moderator` has all permissions from `reviewer`, `contributor`, `viewer`
- etc.

## Security Considerations

### AI Model Protection

- **Only `admin` role can modify AI models**
- Critical models (Claude-3, GPT-4) have additional protection
- All model modifications are logged for audit

### Permission Validation

- Client-side UI shows/hides features based on permissions
- Server-side validation enforces permissions on all operations
- Role assignments are cached and refreshed automatically

### Audit Trail

All access control events are logged:
```javascript
{
  timestamp: "2025-01-07T10:30:00Z",
  user: "username",
  role: "contributor", 
  action: "model.update",
  resource: "claude-3-sonnet",
  result: "denied",
  reason: "insufficient_permissions"
}
```

## Troubleshooting

### User Not Getting Expected Role

1. Check if user is assigned custom role in repository settings
2. Verify role name matches mapping (e.g., `llmxive-admin`)
3. Check if user accepted repository invitation
4. Verify user has authenticated with llmXive

### Permission Denied Errors

1. Confirm user's assigned role has required permission
2. Check if action requires higher role level
3. Verify user is authenticated and session is valid
4. Review audit logs for access control events

### Role Assignment Issues

1. Ensure repository owner has admin access to assign roles
2. Check GitHub API rate limits
3. Verify organization settings allow custom roles
4. Confirm user exists and username is correct

## Future Enhancements

- **Dynamic Role Management**: Web interface for role assignment
- **Temporary Permissions**: Time-limited role assignments  
- **Project-Specific Roles**: Different permissions per project
- **API Integration**: Automated role assignment based on contributions

This role-based system ensures that llmXive maintains security while providing appropriate access levels for different types of users in the research community.