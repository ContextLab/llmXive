# Authentication & Access Control

## Overview

llmXive uses GitHub OAuth for authentication and implements role-based access control to ensure only authorized users can modify AI models and perform sensitive operations.

## Authentication Flow

### 1. GitHub OAuth Integration

```javascript
// In production, users authenticate via GitHub OAuth
// This uses the existing Heroku proxy for token exchange
const authUrl = 'https://github.com/login/oauth/authorize';
const proxyUrl = 'https://llmxive-auth-b300c94fab60.herokuapp.com/authenticate/';
```

### 2. User Login Process

1. User clicks "Login with GitHub" button
2. Redirected to GitHub OAuth authorization page
3. GitHub redirects back with authorization code
4. Code is exchanged for access token via Heroku proxy
5. User profile and repository permissions are fetched
6. User role is automatically assigned based on repository access

## Role-Based Access Control (RBAC)

### Role Hierarchy

The system implements a 5-level role hierarchy based on GitHub repository permissions:

| Role | Level | Description | GitHub Permission |
|------|-------|-------------|------------------|
| **Admin** | 100 | Full system access, can modify AI models | Repository admin/owner |
| **Moderator** | 50 | Can moderate content and reviews | Write/maintain access |
| **Contributor** | 30 | Can create projects and submit reviews | Has commits in repo |
| **Viewer** | 10 | Read-only access to public content | Authenticated user |
| **Anonymous** | 0 | Limited public access | Not authenticated |

### Role Assignment Logic

```javascript
async determineUserRole(user) {
    // Check repository admin/owner status
    if (await this.isRepositoryAdmin(user)) {
        return 'admin';
    }
    
    // Check collaborator with write access
    if (await this.isRepositoryCollaborator(user)) {
        return 'moderator';
    }
    
    // Check if user has contributed
    if (await this.isContributor(user)) {
        return 'contributor';
    }
    
    // Default for authenticated users
    return 'viewer';
}
```

## AI Model Modification Security

### Admin-Only Model Modifications

**Only users with admin role can modify AI models:**

- ✅ **Allowed for Admins:**
  - Add new AI models
  - Update model configurations
  - Remove/archive models
  - Configure model settings

- ❌ **Denied for All Other Roles:**
  - Viewers: Cannot modify models
  - Contributors: Cannot modify models
  - Moderators: Cannot modify models

### Critical Model Protection

Certain models require additional protection:

```javascript
const criticalModels = [
    'claude-3-opus',
    'claude-3-sonnet', 
    'gpt-4',
    'gpt-4-turbo'
];
```

Critical models have enhanced security:
- Require explicit admin role verification
- Additional audit logging
- Cannot be removed while in active use

### Permission Validation

```javascript
// Example: Model modification security check
async updateModel(modelId, updates) {
    // Primary security check
    this.accessControl.requirePermission('model.update', 'modify AI model');
    
    // Additional critical model check
    if (!this.accessControl.canModifyModel(modelId, 'update')) {
        throw new AccessControlError(
            'Insufficient permissions to modify this model',
            'model.update.critical',
            this.accessControl.userRole
        );
    }
    
    // Log security event
    this.accessControl.logAccessEvent('model.update', modelId, true, { updates });
    
    // Proceed with modification...
}
```

## Testing the System

### Demo Mode (Development)

For testing and demonstration, the system includes a demo mode with simulated users:

```javascript
const DEMO_USERS = {
    'viewer': { role: 'viewer', name: 'Demo Viewer' },
    'contributor': { role: 'contributor', name: 'Demo Contributor' },
    'moderator': { role: 'moderator', name: 'Demo Moderator' },
    'admin': { role: 'admin', name: 'Demo Admin' }
};
```

### Testing Access Control

1. **Open the web interface**: `http://localhost:8001/simple-demo.html`
2. **Click "Login with GitHub"** to see role selection modal
3. **Select different roles** to test permission levels:
   - Try editing models as a viewer (denied)
   - Try editing models as an admin (allowed)

### Command Line Tests

Run the automated test suite:

```bash
node test-access-control.js
```

Expected output:
```
🔒 Access Control Test Suite
===========================
✅ Anonymous: Model modification correctly denied
✅ Viewer: Model modification correctly denied  
✅ Contributor: Model modification correctly denied
✅ Moderator: Model modification correctly denied
✅ Admin: Model modification correctly allowed
🎉 All tests passed!
```

## Security Features

### 1. Permission Validation

All sensitive operations validate permissions:

```javascript
// Check specific permission
if (!accessControl.hasPermission('model.update')) {
    throw new AccessControlError('Insufficient permissions');
}

// Check minimum role level
if (!accessControl.hasMinimumRole('admin')) {
    throw new AccessControlError('Admin role required');
}
```

### 2. UI Permission Indicators

The interface shows permission status:

```html
<!-- Denied state -->
<span class="permission-indicator denied">
    <i class="fas fa-lock"></i> Admin Only
</span>

<!-- Allowed state -->
<span class="permission-indicator allowed">
    <i class="fas fa-check"></i> Allowed
</span>
```

### 3. Audit Logging

All access control events are logged:

```javascript
logAccessEvent(action, resource, result, details = {}) {
    const logEntry = {
        timestamp: new Date().toISOString(),
        user: this.client?.getCurrentUser()?.login || 'anonymous',
        role: this.userRole,
        action,
        resource,
        result: result ? 'allowed' : 'denied',
        details
    };
    
    // Log to security audit trail
    this.client.logSecurityEvent(logEntry);
}
```

## Production Deployment

### Environment Variables

Set up GitHub OAuth application and configure:

```bash
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_REDIRECT_URI=https://your-domain.com/auth/callback
```

### Repository Configuration

1. **Set up GitHub OAuth App** in repository settings
2. **Configure repository collaborators** with appropriate permissions
3. **Add admin users** as repository admins/owners
4. **Review audit logs** regularly for security monitoring

### Security Considerations

- ✅ All model modifications require admin permissions
- ✅ Critical models have additional protection layers
- ✅ All security events are logged for audit trails
- ✅ Role assignment is automatic based on GitHub permissions
- ✅ Permission checks occur both client-side and server-side
- ✅ CSRF protection through OAuth state parameters

## Error Handling

The system provides clear error messages for permission violations:

```javascript
// Example error messages
"Access Denied: Only administrators can add new AI models."
"Access Denied: Only administrators can modify AI models. Current role: viewer"
"Insufficient permissions to modify this model. Required: model.update"
```

## Conclusion

This access control system ensures that:

1. **Only admin users can modify AI models** - protecting against unauthorized changes
2. **Role assignment is automatic** - based on GitHub repository permissions  
3. **Critical models have extra protection** - preventing accidental modifications
4. **All actions are audited** - providing complete security trail
5. **The UI clearly shows permissions** - users understand their access level

The system balances security with usability, ensuring that sensitive operations like AI model modification are properly protected while allowing appropriate access for collaboration and research.