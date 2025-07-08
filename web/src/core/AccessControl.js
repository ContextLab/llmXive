/**
 * Access Control Manager for llmXive
 * 
 * Handles role-based permissions and security for sensitive operations
 */

export class AccessControl {
    constructor(client) {
        this.client = client;
        this.userRole = null;
        this.permissions = null;
        
        // Define role hierarchy and permissions
        // Updated to match GitHub custom repository roles
        this.roleDefinitions = {
            'admin': {
                level: 100,
                description: 'Full system administrator',
                permissions: [
                    'model.create',
                    'model.update', 
                    'model.delete',
                    'model.configure',
                    'user.manage',
                    'role.assign',
                    'moderation.manage',
                    'system.configure',
                    'project.create',
                    'project.update',
                    'project.delete',
                    'review.create',
                    'review.approve',
                    'review.reject',
                    'vote.cast',
                    'idea.submit'
                ]
            },
            'moderator': {
                level: 70,
                description: 'Content and review moderator',
                permissions: [
                    'model.view',
                    'moderation.review',
                    'moderation.approve',
                    'moderation.reject',
                    'project.create',
                    'project.update',
                    'review.create',
                    'review.approve',
                    'review.moderate',
                    'vote.cast',
                    'idea.submit'
                ]
            },
            'reviewer': {
                level: 50,
                description: 'Trusted reviewer with approval permissions',
                permissions: [
                    'model.view',
                    'project.create',
                    'project.update',
                    'review.create',
                    'review.approve',
                    'vote.cast',
                    'idea.submit'
                ]
            },
            'contributor': {
                level: 30,
                description: 'Default authenticated user (can submit reviews, ideas, vote)',
                permissions: [
                    'model.view',
                    'project.view',
                    'project.create',
                    'review.create',
                    'review.submit',
                    'vote.cast',
                    'idea.submit'
                ]
            },
            'viewer': {
                level: 10,
                description: 'Read-only access',
                permissions: [
                    'model.view',
                    'project.view',
                    'review.view'
                ]
            },
            'anonymous': {
                level: 0,
                description: 'Unauthenticated user',
                permissions: [
                    'project.view',
                    'review.view'
                ]
            }
        };
    }
    
    /**
     * Initialize access control with user authentication
     */
    async initialize(user = null) {
        try {
            if (!user) {
                this.userRole = 'anonymous';
                this.permissions = this.roleDefinitions.anonymous.permissions;
                return { role: this.userRole, permissions: this.permissions };
            }
            
            // Determine user role based on GitHub user data
            this.userRole = await this.determineUserRole(user);
            this.permissions = this.roleDefinitions[this.userRole]?.permissions || [];
            
            console.log(`Access control initialized: ${user.login} -> ${this.userRole}`);
            
            return {
                role: this.userRole,
                permissions: this.permissions,
                level: this.roleDefinitions[this.userRole]?.level || 0
            };
            
        } catch (error) {
            console.error('Failed to initialize access control:', error);
            // Fallback to anonymous permissions
            this.userRole = 'anonymous';
            this.permissions = this.roleDefinitions.anonymous.permissions;
            return { role: this.userRole, permissions: this.permissions };
        }
    }
    
    /**
     * Determine user role based on GitHub custom repository roles
     * Uses https://github.com/ContextLab/llmXive/settings/access
     */
    async determineUserRole(user) {
        try {
            // First check if user is repository owner (always admin)
            if (await this.isRepositoryOwner(user)) {
                return 'admin';
            }
            
            // Check custom repository roles from GitHub settings
            const customRole = await this.getCustomRepositoryRole(user);
            if (customRole) {
                return this.mapCustomRoleToSystemRole(customRole);
            }
            
            // Check if user is a standard collaborator
            const collaboratorRole = await this.getCollaboratorRole(user);
            if (collaboratorRole) {
                return this.mapCollaboratorRoleToSystemRole(collaboratorRole);
            }
            
            // Default role for authenticated users (can submit reviews, ideas, vote)
            return 'contributor';
            
        } catch (error) {
            console.error('Error determining user role:', error);
            // Default to contributor for authenticated users
            return 'contributor';
        }
    }
    
    /**
     * Check if user is repository owner
     */
    async isRepositoryOwner(user) {
        try {
            const repo = await this.client.getRepository();
            return repo.owner && repo.owner.login === user.login;
        } catch (error) {
            console.warn('Could not check owner status:', error);
            return false;
        }
    }

    /**
     * Get custom repository role from GitHub settings/access
     * Uses the Repository Access API to check custom roles
     */
    async getCustomRepositoryRole(user) {
        try {
            // Check custom repository roles via GitHub API
            // This uses the repository invitation/collaborator API
            const response = await this.client.github.request('GET /repos/{owner}/{repo}/collaborators/{username}', {
                owner: this.client.options.owner,
                repo: this.client.options.repo,
                username: user.login
            });

            // GitHub custom roles are returned in the role_name field
            if (response.data && response.data.role_name) {
                return response.data.role_name;
            }

            // Also check via the repository access API if available
            const accessResponse = await this.client.github.request('GET /repos/{owner}/{repo}/collaborators/{username}/permission', {
                owner: this.client.options.owner,
                repo: this.client.options.repo,
                username: user.login
            });

            return accessResponse.data?.role_name || null;
            
        } catch (error) {
            // User might not have any custom role assigned
            console.debug(`No custom role found for ${user.login}:`, error);
            return null;
        }
    }

    /**
     * Get standard collaborator role
     */
    async getCollaboratorRole(user) {
        try {
            const collaborator = await this.client.getCollaboratorPermission(user.login);
            return collaborator?.permission || null;
        } catch (error) {
            console.debug(`Not a collaborator: ${user.login}`, error);
            return null;
        }
    }

    /**
     * Map GitHub custom role names to system roles
     */
    mapCustomRoleToSystemRole(customRole) {
        // Map GitHub custom role names to our internal role system
        const roleMapping = {
            // Custom roles that can be defined in GitHub Settings > Access
            'llmxive-admin': 'admin',
            'llmxive-moderator': 'moderator', 
            'llmxive-reviewer': 'reviewer',
            'llmxive-contributor': 'contributor',
            'llmxive-viewer': 'viewer',
            
            // Alternative naming conventions
            'admin': 'admin',
            'moderator': 'moderator',
            'reviewer': 'reviewer',
            'contributor': 'contributor',
            'viewer': 'viewer',
            
            // Legacy role names
            'maintainer': 'moderator',
            'collaborator': 'contributor',
            'read': 'viewer'
        };

        const mappedRole = roleMapping[customRole.toLowerCase()];
        if (mappedRole) {
            console.log(`Mapped custom role '${customRole}' to system role '${mappedRole}'`);
            return mappedRole;
        }

        // If custom role doesn't match our mapping, default to contributor
        console.warn(`Unknown custom role '${customRole}', defaulting to contributor`);
        return 'contributor';
    }

    /**
     * Map standard GitHub collaborator permissions to system roles
     */
    mapCollaboratorRoleToSystemRole(permission) {
        const permissionMapping = {
            'admin': 'moderator',      // GitHub admin -> llmXive moderator (not full admin)
            'maintain': 'moderator',   // GitHub maintain -> llmXive moderator
            'write': 'contributor',    // GitHub write -> llmXive contributor  
            'triage': 'contributor',   // GitHub triage -> llmXive contributor
            'read': 'viewer'           // GitHub read -> llmXive viewer
        };

        const mappedRole = permissionMapping[permission];
        if (mappedRole) {
            console.log(`Mapped collaborator permission '${permission}' to system role '${mappedRole}'`);
            return mappedRole;
        }

        // Default to contributor for unknown permissions
        return 'contributor';
    }
    
    /**
     * Check if user is a repository collaborator with write access
     */
    async isRepositoryCollaborator(user) {
        try {
            const collaborator = await this.client.getCollaboratorPermission(user.login);
            return ['write', 'maintain', 'admin'].includes(collaborator?.permission);
            
        } catch (error) {
            console.warn('Could not check collaborator status:', error);
            return false;
        }
    }
    
    /**
     * Check if user has contributed to the repository
     */
    async isContributor(user) {
        try {
            const contributors = await this.client.getContributors();
            return contributors.some(contributor => contributor.login === user.login);
            
        } catch (error) {
            console.warn('Could not check contributor status:', error);
            return false;
        }
    }
    
    /**
     * Check if user has a specific permission
     */
    hasPermission(permission) {
        if (!this.permissions) {
            return false;
        }
        
        return this.permissions.includes(permission);
    }
    
    /**
     * Check if user has minimum role level
     */
    hasMinimumRole(requiredRole) {
        const userLevel = this.roleDefinitions[this.userRole]?.level || 0;
        const requiredLevel = this.roleDefinitions[requiredRole]?.level || 0;
        
        return userLevel >= requiredLevel;
    }
    
    /**
     * Require specific permission (throws error if not authorized)
     */
    requirePermission(permission, operation = 'perform this action') {
        if (!this.hasPermission(permission)) {
            throw new AccessControlError(
                `Insufficient permissions to ${operation}. Required: ${permission}`,
                permission,
                this.userRole
            );
        }
    }
    
    /**
     * Require minimum role (throws error if not authorized)
     */
    requireRole(requiredRole, operation = 'perform this action') {
        if (!this.hasMinimumRole(requiredRole)) {
            throw new AccessControlError(
                `Insufficient role to ${operation}. Required: ${requiredRole}, Current: ${this.userRole}`,
                `role.${requiredRole}`,
                this.userRole
            );
        }
    }
    
    /**
     * Check model modification permissions with additional security
     */
    canModifyModel(modelId, operation = 'modify') {
        try {
            // Only admins can modify AI models
            this.requirePermission('model.update', `${operation} AI model`);
            
            // Additional checks for critical models
            if (this.isCriticalModel(modelId)) {
                this.requireRole('admin', `${operation} critical AI model`);
            }
            
            return true;
            
        } catch (error) {
            console.warn(`Model modification denied: ${error.message}`);
            return false;
        }
    }
    
    /**
     * Check if model is considered critical (requires higher permissions)
     */
    isCriticalModel(modelId) {
        const criticalModels = [
            'claude-3-opus',
            'claude-3-sonnet', 
            'gpt-4',
            'gpt-4-turbo'
        ];
        
        return criticalModels.some(critical => 
            modelId && modelId.toLowerCase().includes(critical.toLowerCase())
        );
    }
    
    /**
     * Get user's current role and permissions info
     */
    getUserInfo() {
        return {
            role: this.userRole,
            permissions: this.permissions,
            level: this.roleDefinitions[this.userRole]?.level || 0,
            canModifyModels: this.hasPermission('model.update'),
            canManageUsers: this.hasPermission('user.manage'),
            canManageModeration: this.hasPermission('moderation.manage')
        };
    }
    
    /**
     * Log access control event for audit trail
     */
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
        
        console.log('Access Control Event:', logEntry);
        
        // In production, this would be sent to an audit log
        if (this.client && this.client.logSecurityEvent) {
            this.client.logSecurityEvent(logEntry);
        }
    }
}

/**
 * Custom error class for access control violations
 */
export class AccessControlError extends Error {
    constructor(message, requiredPermission, userRole) {
        super(message);
        this.name = 'AccessControlError';
        this.requiredPermission = requiredPermission;
        this.userRole = userRole;
    }
}

export default AccessControl;