#!/usr/bin/env node

/**
 * Comprehensive Project Links and Files Audit Script
 * 
 * This script systematically checks:
 * 1. All project document links in database vs actual file locations
 * 2. Misplaced files in the repository
 * 3. GitHub URLs consistency
 * 4. Missing or broken document paths
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Starting comprehensive project audit...\n');

// Load project database
let projects;
try {
    const projectsData = fs.readFileSync('database/projects.json', 'utf8');
    projects = JSON.parse(projectsData).projects;
} catch (error) {
    console.error('❌ Failed to load projects database:', error.message);
    process.exit(1);
}

const issues = [];
const suggestions = [];

// Function to check if file exists
function fileExists(filePath) {
    try {
        return fs.statSync(filePath).isFile();
    } catch {
        return false;
    }
}

// Function to recursively find files
function findFiles(dir, pattern) {
    const results = [];
    if (!fs.existsSync(dir)) return results;
    
    const files = fs.readdirSync(dir);
    for (const file of files) {
        const fullPath = path.join(dir, file);
        const stat = fs.statSync(fullPath);
        
        if (stat.isDirectory()) {
            results.push(...findFiles(fullPath, pattern));
        } else if (file.match(pattern)) {
            results.push(fullPath);
        }
    }
    return results;
}

console.log('📋 Analyzing project database...');

// 1. Check each project's document locations
Object.entries(projects).forEach(([projectId, project]) => {
    console.log(`\n🔍 Checking project: ${projectId}`);
    console.log(`   Title: ${project.title}`);
    
    // Check documented location
    if (project.location) {
        const fullPath = project.location;
        console.log(`   Documented location: ${fullPath}`);
        
        if (!fileExists(fullPath)) {
            issues.push({
                type: 'missing_file',
                project: projectId,
                message: `Documented file missing: ${fullPath}`,
                severity: 'high'
            });
        }
    } else {
        issues.push({
            type: 'no_location',
            project: projectId,
            message: 'No location specified in database',
            severity: 'medium'
        });
    }
    
    // Check for common document patterns
    const expectedPaths = [
        `technical_design_documents/${projectId}/design.md`,
        `technical_design_documents/${projectId}/design-completed.md`,
        `implementation_plans/${projectId}/plan.md`,
        `papers/${projectId}/paper.pdf`,
        `code/${projectId}/`,
        `reviews/${projectId}/`
    ];
    
    expectedPaths.forEach(expectedPath => {
        if (fileExists(expectedPath)) {
            console.log(`   ✅ Found: ${expectedPath}`);
            
            // Check if this matches the documented location
            if (project.location && project.location !== expectedPath) {
                issues.push({
                    type: 'location_mismatch',
                    project: projectId,
                    message: `Database says "${project.location}" but found "${expectedPath}"`,
                    severity: 'medium'
                });
            }
        }
    });
    
    // Check GitHub issue link
    if (project.githubIssue) {
        console.log(`   GitHub Issue: #${project.githubIssue}`);
    }
});

console.log('\n📁 Scanning for misplaced files...');

// 2. Find all design documents and check their locations
const allMarkdownFiles = findFiles('.', /\.(md|pdf)$/);
const webFolderDocs = allMarkdownFiles.filter(file => 
    file.startsWith('./technical_design_documents') && 
    file.includes('/web/')
);

if (webFolderDocs.length > 0) {
    issues.push({
        type: 'misplaced_files',
        message: `Found ${webFolderDocs.length} design documents in web/ folder`,
        files: webFolderDocs,
        severity: 'high'
    });
}

// 3. Check for orphaned documents (files not referenced in database)
console.log('\n🔍 Looking for orphaned documents...');

const referencedFiles = new Set();
Object.values(projects).forEach(project => {
    if (project.location) {
        referencedFiles.add(project.location);
    }
    // Add review files
    if (project.reviews) {
        project.reviews.forEach(review => {
            if (review.location) {
                referencedFiles.add(review.location);
            }
        });
    }
});

const allProjectDocs = findFiles('./technical_design_documents', /\.md$/);
const allImplementationPlans = findFiles('./implementation_plans', /\.md$/);
const allPapers = findFiles('./papers', /\.pdf$/);

const allDocuments = [...allProjectDocs, ...allImplementationPlans, ...allPapers];
const orphanedDocs = allDocuments.filter(doc => !referencedFiles.has(doc.replace('./', '')));

if (orphanedDocs.length > 0) {
    suggestions.push({
        type: 'orphaned_documents',
        message: `Found ${orphanedDocs.length} documents not referenced in database`,
        files: orphanedDocs
    });
}

// 4. Generate document path mapping for centralized management
console.log('\n📝 Generating centralized document path mapping...');

const documentMapping = {};
Object.entries(projects).forEach(([projectId, project]) => {
    const mapping = {};
    
    // Find actual design document
    const designPaths = [
        `technical_design_documents/${projectId}/design.md`,
        `technical_design_documents/${projectId}/design-completed.md`,
        project.location
    ].filter(Boolean);
    
    for (const designPath of designPaths) {
        if (fileExists(designPath)) {
            mapping.design = designPath;
            break;
        }
    }
    
    // Find implementation plan
    const implPath = `implementation_plans/${projectId}/plan.md`;
    if (fileExists(implPath)) {
        mapping.implementation = implPath;
    }
    
    // Find paper
    const paperPath = `papers/${projectId}/paper.pdf`;
    if (fileExists(paperPath)) {
        mapping.paper = paperPath;
    }
    
    // Find code
    const codePath = `code/${projectId}/`;
    if (fs.existsSync(codePath)) {
        mapping.code = codePath;
    }
    
    if (Object.keys(mapping).length > 0) {
        documentMapping[projectId] = mapping;
    }
});

// Generate report
console.log('\n' + '='.repeat(60));
console.log('📊 AUDIT REPORT');
console.log('='.repeat(60));

console.log(`\n🔴 ISSUES FOUND (${issues.length}):`);
issues.forEach((issue, index) => {
    console.log(`\n${index + 1}. [${issue.severity.toUpperCase()}] ${issue.type}`);
    console.log(`   Project: ${issue.project || 'General'}`);
    console.log(`   Message: ${issue.message}`);
    if (issue.files) {
        console.log(`   Files: ${issue.files.join(', ')}`);
    }
});

console.log(`\n💡 SUGGESTIONS (${suggestions.length}):`);
suggestions.forEach((suggestion, index) => {
    console.log(`\n${index + 1}. ${suggestion.type}`);
    console.log(`   ${suggestion.message}`);
    if (suggestion.files) {
        console.log(`   Files: ${suggestion.files.slice(0, 5).join(', ')}${suggestion.files.length > 5 ? '...' : ''}`);
    }
});

// Write document mapping to file
const mappingContent = `// Auto-generated document path mapping
// Generated on ${new Date().toISOString()}

export const DOCUMENT_PATHS = ${JSON.stringify(documentMapping, null, 2)};

// GitHub base URL for fallback links
export const GITHUB_BASE = 'https://github.com/ContextLab/llmXive/blob/main';

// Get document URL for a project
export function getDocumentUrl(projectId, documentType) {
    const mapping = DOCUMENT_PATHS[projectId];
    if (!mapping || !mapping[documentType]) {
        return null;
    }
    return mapping[documentType];
}

// Get GitHub URL for a document
export function getGitHubUrl(filePath) {
    return \`\${GITHUB_BASE}/\${filePath}\`;
}
`;

fs.writeFileSync('src/data/DocumentPaths.js', mappingContent);
console.log('\n✅ Generated centralized document mapping: src/data/DocumentPaths.js');

console.log('\n📋 SUMMARY:');
console.log(`   - Projects analyzed: ${Object.keys(projects).length}`);
console.log(`   - Issues found: ${issues.length}`);
console.log(`   - Suggestions: ${suggestions.length}`);
console.log(`   - Documents mapped: ${Object.keys(documentMapping).length}`);

if (issues.length > 0) {
    console.log('\n⚠️  Repository cleanup needed!');
    process.exit(1);
} else {
    console.log('\n✅ No critical issues found!');
    process.exit(0);
}