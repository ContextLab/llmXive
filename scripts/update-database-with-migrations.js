#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const BASE_PATH = '/Users/jmanning/llmXive';
const DATABASE_PATH = path.join(BASE_PATH, 'web/database/projects.json');
const MIGRATION_REPORT = path.join(BASE_PATH, 'migration-report-phase2.json');

// Read existing database
const database = JSON.parse(fs.readFileSync(DATABASE_PATH, 'utf8'));

// Read migration report
const migrationReport = JSON.parse(fs.readFileSync(MIGRATION_REPORT, 'utf8'));

// Function to determine field from project type and name
function determineField(type, name) {
    if (name.includes('biology')) return 'biology';
    if (name.includes('chemistry')) return 'chemistry';
    if (name.includes('materials-science')) return 'materials-science';
    if (name.includes('energy')) return 'energy';
    if (name.includes('environmental')) return 'environmental-science';
    if (name.includes('agriculture')) return 'agriculture';
    if (name.includes('psychology')) return 'psychology';
    if (name.includes('computer-science')) return 'computer-science';
    if (name.includes('robotics')) return 'robotics';
    if (name.includes('gene-regulation')) return 'biology';
    if (name.includes('neural-plasticity')) return 'neuroscience';
    if (name.includes('automation')) return 'computer-science';
    return 'general';
}

// Function to determine phase from project type
function determinePhase(type) {
    switch (type) {
        case 'papers': return 'completed';
        case 'technical_design_documents': return 'design';
        case 'implementation_plans': return 'implementation';
        case 'code': return 'development';
        case 'reviews': return 'review';
        default: return 'design';
    }
}

// Function to determine status from project type
function determineStatus(type) {
    switch (type) {
        case 'papers': return 'done';
        case 'technical_design_documents': return 'ready';
        case 'implementation_plans': return 'in-progress';
        case 'code': return 'in-progress';
        case 'reviews': return 'ready';
        default: return 'ready';
    }
}

// Add new projects to database
const newProjects = migrationReport.projects.map(project => {
    const field = determineField(project.type, project.name);
    const phase = determinePhase(project.type);
    const status = determineStatus(project.type);
    
    return {
        id: project.id,
        title: project.name.replace(/-/g, ' '),
        description: `Migrated project: ${project.name}`,
        field: field,
        status: status,
        phase: phase,
        githubIssue: null,
        dateCreated: new Date().toISOString(),
        dateModified: new Date().toISOString(),
        contributors: [],
        completeness: 16,
        keywords: generateKeywords(project.name, field),
        dependencies: generateDependencies(field),
        location: `projects/${project.id}/`,
        estimatedTimeline: generateTimeline(phase),
        reviews: []
    };
});

function generateKeywords(name, field) {
    const baseKeywords = {
        'biology': ['genomics', 'bioinformatics', 'molecular-biology'],
        'chemistry': ['materials', 'synthesis', 'analysis'],
        'materials-science': ['nanomaterials', 'composites', 'characterization'],
        'energy': ['renewable', 'efficiency', 'storage'],
        'environmental-science': ['climate', 'sustainability', 'monitoring'],
        'agriculture': ['precision-farming', 'IoT', 'sustainability'],
        'psychology': ['mental-health', 'cognitive-science', 'behavior'],
        'computer-science': ['AI', 'machine-learning', 'algorithms'],
        'robotics': ['autonomous-systems', 'control-systems', 'sensors'],
        'neuroscience': ['neural-networks', 'brain-imaging', 'cognition']
    };
    
    const keywords = baseKeywords[field] || ['research', 'analysis', 'development'];
    if (name.includes('automation')) keywords.push('automation');
    if (name.includes('regulation')) keywords.push('regulation');
    if (name.includes('plasticity')) keywords.push('plasticity');
    
    return keywords;
}

function generateDependencies(field) {
    const baseDependencies = {
        'biology': ['Laboratory equipment', 'Genomic databases', 'Bioinformatics tools'],
        'chemistry': ['Chemical synthesis equipment', 'Analytical instruments', 'Safety protocols'],
        'materials-science': ['Material characterization tools', 'Synthesis equipment', 'Testing facilities'],
        'energy': ['Energy systems', 'Monitoring equipment', 'Modeling software'],
        'environmental-science': ['Environmental monitoring', 'GIS software', 'Satellite data'],
        'agriculture': ['IoT sensors', 'Agricultural data', 'Machine learning platforms'],
        'psychology': ['Clinical partnerships', 'Survey platforms', 'Statistical software'],
        'computer-science': ['Computing resources', 'Software frameworks', 'Development tools'],
        'robotics': ['Robotics hardware', 'ROS framework', 'Sensor systems'],
        'neuroscience': ['Neuroimaging equipment', 'Data analysis tools', 'Clinical collaboration']
    };
    
    return baseDependencies[field] || ['Research resources', 'Data access', 'Computing infrastructure'];
}

function generateTimeline(phase) {
    const today = new Date();
    const start = today.toISOString().split('T')[0];
    
    const endDate = new Date(today);
    switch (phase) {
        case 'completed':
            endDate.setFullYear(today.getFullYear() + 1);
            break;
        case 'design':
            endDate.setFullYear(today.getFullYear() + 2);
            break;
        case 'implementation':
            endDate.setFullYear(today.getFullYear() + 3);
            break;
        case 'development':
            endDate.setFullYear(today.getFullYear() + 2);
            break;
        default:
            endDate.setFullYear(today.getFullYear() + 2);
    }
    
    return `${start} to ${endDate.toISOString().split('T')[0]}`;
}

// Add new projects to existing database
database.projects.push(...newProjects);

// Update metadata
database.metadata.totalProjects = database.projects.length;
database.metadata.lastUpdated = new Date().toISOString();
database.metadata.version = "2.1.0";
database.metadata.description = "llmXive Projects Database - Updated with Phase 2 migrations";

// Write updated database
fs.writeFileSync(DATABASE_PATH, JSON.stringify(database, null, 2));

console.log(`Database updated successfully!`);
console.log(`Total projects: ${database.projects.length}`);
console.log(`Added ${newProjects.length} new projects from migration`);

// Print summary
console.log('\n=== NEW PROJECTS ADDED ===');
newProjects.forEach(project => {
    console.log(`✓ ${project.id} (${project.title}) - ${project.field} - ${project.status}`);
});