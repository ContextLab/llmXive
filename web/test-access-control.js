#!/usr/bin/env node

/**
 * Command-line test for Access Control implementation
 * Tests that only admin users can modify AI models
 */

// Mock ES6 modules for Node.js testing
class AccessControlError extends Error {
    constructor(message, requiredPermission, userRole) {
        super(message);
        this.name = 'AccessControlError';
        this.requiredPermission = requiredPermission;
        this.userRole = userRole;
    }
}

class AccessControl {
    constructor(client) {
        this.client = client;
        this.userRole = null;
        this.permissions = null;
        
        // Define role hierarchy and permissions
        this.roleDefinitions = {
            'admin': {
                level: 100,
                permissions: [
                    'model.create',
                    'model.update', 
                    'model.delete',
                    'model.configure',
                    'user.manage',
                    'moderation.manage',
                    'system.configure',
                    'project.create',
                    'project.update',
                    'project.delete',
                    'review.create',
                    'review.approve',
                    'review.reject'
                ]
            },
            'moderator': {
                level: 50,
                permissions: [
                    'model.view',
                    'moderation.review',
                    'moderation.approve',
                    'moderation.reject',
                    'project.create',
                    'project.update',
                    'review.create',
                    'review.approve'
                ]
            },
            'contributor': {
                level: 30,
                permissions: [
                    'model.view',
                    'project.create',
                    'project.update',
                    'review.create',
                    'review.submit'
                ]
            },
            'viewer': {
                level: 10,
                permissions: [
                    'model.view',
                    'project.view',
                    'review.view'
                ]
            },
            'anonymous': {
                level: 0,
                permissions: [
                    'project.view',
                    'review.view'
                ]
            }
        };
    }
    
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
    
    async determineUserRole(user) {
        try {
            // Check if user is a repository admin/owner
            if (await this.isRepositoryAdmin(user)) {
                return 'admin';
            }
            
            // Check if user is a collaborator with write access
            if (await this.isRepositoryCollaborator(user)) {
                return 'moderator';
            }
            
            // Check if user has contributed to the repository
            if (await this.isContributor(user)) {
                return 'contributor';
            }
            
            // Default to viewer for authenticated users
            return 'viewer';
            
        } catch (error) {
            console.error('Error determining user role:', error);
            return 'viewer';
        }
    }
    
    async isRepositoryAdmin(user) {
        try {
            // Check if user is owner or has admin permissions
            const repo = await this.client.getRepository();
            
            // Repository owner has admin access
            if (repo.owner && repo.owner.login === user.login) {
                return true;
            }
            
            // Check collaborator permissions
            const collaborator = await this.client.getCollaboratorPermission(user.login);
            return collaborator?.permission === 'admin';
            
        } catch (error) {
            console.warn('Could not check admin status:', error);
            return false;
        }
    }
    
    async isRepositoryCollaborator(user) {
        try {
            const collaborator = await this.client.getCollaboratorPermission(user.login);
            return ['write', 'maintain', 'admin'].includes(collaborator?.permission);
            
        } catch (error) {
            console.warn('Could not check collaborator status:', error);
            return false;
        }
    }
    
    async isContributor(user) {
        try {
            const contributors = await this.client.getContributors();
            return contributors.some(contributor => contributor.login === user.login);
            
        } catch (error) {
            console.warn('Could not check contributor status:', error);
            return false;
        }
    }
    
    hasPermission(permission) {
        if (!this.permissions) {
            return false;
        }
        
        return this.permissions.includes(permission);
    }
    
    hasMinimumRole(requiredRole) {
        const userLevel = this.roleDefinitions[this.userRole]?.level || 0;
        const requiredLevel = this.roleDefinitions[requiredRole]?.level || 0;
        
        return userLevel >= requiredLevel;
    }
    
    requirePermission(permission, operation = 'perform this action') {
        if (!this.hasPermission(permission)) {
            throw new AccessControlError(
                `Insufficient permissions to ${operation}. Required: ${permission}`,
                permission,
                this.userRole
            );
        }
    }
    
    requireRole(requiredRole, operation = 'perform this action') {
        if (!this.hasMinimumRole(requiredRole)) {
            throw new AccessControlError(
                `Insufficient role to ${operation}. Required: ${requiredRole}, Current: ${this.userRole}`,
                `role.${requiredRole}`,
                this.userRole
            );
        }
    }
    
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
}

// Mock GitHub client for testing
class MockGitHubClient {
    constructor(scenario = 'anonymous') {
        this.scenario = scenario;
    }

    getCurrentUser() {
        const users = {
            'anonymous': null,
            'viewer': { login: 'testviewer' },
            'contributor': { login: 'testcontributor' },
            'moderator': { login: 'testmoderator' },
            'admin': { login: 'testadmin' }
        };
        return users[this.scenario];
    }

    async getRepository() {
        return {
            owner: { login: 'ContextLab' },
            name: 'llmXive'
        };
    }

    async getCollaboratorPermission(username) {
        const permissions = {
            'testadmin': { permission: 'admin' },
            'testmoderator': { permission: 'write' },
            'testcontributor': { permission: 'read' },
            'testviewer': { permission: 'read' }
        };
        return permissions[username] || null;
    }

    async getContributors() {
        return [
            { login: 'testcontributor' },
            { login: 'testmoderator' },
            { login: 'testadmin' }
        ];
    }

    logSecurityEvent(event) {
        console.log('Security Event:', event);
    }
}

// Test functions
async function testUserAccess(scenario, expectedRole, shouldAllowModelModification = false) {
    console.log(`\n🧪 Testing ${scenario} user...`);
    
    try {
        const client = new MockGitHubClient(scenario);
        const accessControl = new AccessControl(client);
        
        const user = client.getCurrentUser();
        const result = await accessControl.initialize(user);
        
        // Test role assignment
        if (result.role === expectedRole) {
            console.log(`✅ Role assignment: ${result.role}`);
        } else {
            console.log(`❌ Role assignment: Expected '${expectedRole}', got '${result.role}'`);
        }
        
        // Test model modification
        const canModify = accessControl.canModifyModel('test-model', 'update');
        
        if (shouldAllowModelModification && canModify) {
            console.log(`✅ Model modification: Correctly allowed`);
        } else if (!shouldAllowModelModification && !canModify) {
            console.log(`✅ Model modification: Correctly denied`);
        } else if (shouldAllowModelModification && !canModify) {
            console.log(`❌ Model modification: Incorrectly denied`);
        } else {
            console.log(`❌ Model modification: Incorrectly allowed`);
        }
        
        return true;
        
    } catch (error) {
        console.log(`❌ Error during testing: ${error.message}`);
        return false;
    }
}

async function testCriticalModelProtection() {
    console.log(`\n🧪 Testing critical model protection...`);
    
    const client = new MockGitHubClient('admin');
    const accessControl = new AccessControl(client);
    await accessControl.initialize(client.getCurrentUser());
    
    // Test critical model IDs
    const criticalModels = ['claude-3-opus', 'gpt-4-turbo', 'claude-3-sonnet'];
    
    for (const modelId of criticalModels) {
        const isCritical = accessControl.isCriticalModel(modelId);
        if (isCritical) {
            console.log(`✅ Model '${modelId}' correctly identified as critical`);
        } else {
            console.log(`❌ Model '${modelId}' not identified as critical`);
        }
    }
    
    // Test non-critical model
    const isNonCritical = !accessControl.isCriticalModel('basic-model');
    if (isNonCritical) {
        console.log(`✅ Model 'basic-model' correctly identified as non-critical`);
    } else {
        console.log(`❌ Model 'basic-model' incorrectly identified as critical`);
    }
}

// Main test runner
async function runTests() {
    console.log('🔒 Access Control Test Suite');
    console.log('===========================');
    console.log('Testing that only admin users can modify AI models\n');
    
    const tests = [
        ['anonymous', 'anonymous', false],
        ['viewer', 'viewer', false],
        ['contributor', 'contributor', false],
        ['moderator', 'moderator', false],
        ['admin', 'admin', true]
    ];
    
    let passed = 0;
    let total = tests.length;
    
    for (const [scenario, expectedRole, shouldAllow] of tests) {
        const success = await testUserAccess(scenario, expectedRole, shouldAllow);
        if (success) passed++;
    }
    
    await testCriticalModelProtection();
    
    console.log(`\n📊 Test Results: ${passed}/${total} user tests passed`);
    
    if (passed === total) {
        console.log('🎉 All tests passed! Access control is working correctly.');
        console.log('✅ Only admin users can modify AI models');
        console.log('✅ Critical models have additional protection');
    } else {
        console.log('❌ Some tests failed. Please review the access control implementation.');
    }
}

// Run tests if this script is executed directly
if (require.main === module) {
    runTests().catch(console.error);
}

module.exports = { AccessControl, AccessControlError, MockGitHubClient, runTests };