#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const BASE_PATH = '/Users/jmanning/llmXive';
const PROJECTS_PATH = path.join(BASE_PATH, 'projects');

// Ensure projects directory exists
if (!fs.existsSync(PROJECTS_PATH)) {
    fs.mkdirSync(PROJECTS_PATH, { recursive: true });
}

// Project counter for generating sequential IDs
let projectCounter = 100;

// Find the highest existing project number
const existingProjects = fs.readdirSync(PROJECTS_PATH);
existingProjects.forEach(project => {
    const match = project.match(/^PROJ-(\d+)-/);
    if (match) {
        const num = parseInt(match[1]);
        if (num >= projectCounter && num < 999) {
            projectCounter = num + 1;
        }
    }
});

console.log(`Starting migration with counter: ${projectCounter}`);

function createProjectStructure(projectPath) {
    const dirs = [
        '.llmxive',
        'idea',
        'technical-design', 
        'implementation-plan',
        'code',
        'data',
        'paper',
        'reviews/design',
        'reviews/implementation', 
        'reviews/paper',
        'reviews/code'
    ];
    
    dirs.forEach(dir => {
        const fullPath = path.join(projectPath, dir);
        fs.mkdirSync(fullPath, { recursive: true });
    });
}

function generateProjectId(name) {
    const id = String(projectCounter).padStart(3, '0');
    projectCounter++;
    return `PROJ-${id}-${name}`;
}

function copyDirectory(src, dest) {
    if (!fs.existsSync(dest)) {
        fs.mkdirSync(dest, { recursive: true });
    }
    
    const items = fs.readdirSync(src);
    items.forEach(item => {
        const srcPath = path.join(src, item);
        const destPath = path.join(dest, item);
        
        if (fs.statSync(srcPath).isDirectory()) {
            copyDirectory(srcPath, destPath);
        } else {
            fs.copyFileSync(srcPath, destPath);
        }
    });
}

function migrateProject(sourcePath, projectName, sourceType) {
    const projectId = generateProjectId(projectName);
    const projectPath = path.join(PROJECTS_PATH, projectId);
    
    console.log(`Migrating: ${sourcePath} -> ${projectPath}`);
    
    // Create project structure
    createProjectStructure(projectPath);
    
    // Copy files to appropriate locations based on source type
    if (sourceType === 'papers') {
        copyDirectory(sourcePath, path.join(projectPath, 'paper'));
    } else if (sourceType === 'technical_design_documents') {
        copyDirectory(sourcePath, path.join(projectPath, 'technical-design'));
    } else if (sourceType === 'implementation_plans') {
        copyDirectory(sourcePath, path.join(projectPath, 'implementation-plan'));
    } else if (sourceType === 'reviews') {
        copyDirectory(sourcePath, path.join(projectPath, 'reviews'));
    } else if (sourceType === 'code') {
        copyDirectory(sourcePath, path.join(projectPath, 'code'));
    }
    
    // Create config file
    const config = {
        id: projectId,
        name: projectName,
        created: new Date().toISOString(),
        migrated: true,
        source: sourceType,
        phases: {
            idea: { status: 'pending' },
            technical_design: { status: sourceType === 'technical_design_documents' ? 'completed' : 'pending' },
            implementation_plan: { status: sourceType === 'implementation_plans' ? 'completed' : 'pending' },
            code: { status: sourceType === 'code' ? 'completed' : 'pending' },
            paper: { status: sourceType === 'papers' ? 'completed' : 'pending' },
            reviews: { status: sourceType === 'reviews' ? 'completed' : 'pending' }
        }
    };
    
    fs.writeFileSync(
        path.join(projectPath, '.llmxive', 'config.json'),
        JSON.stringify(config, null, 2)
    );
    
    return projectId;
}

// Migration mapping
const migrations = [
    // Papers
    { 
        source: path.join(BASE_PATH, 'papers', 'gene-regulation-mechanisms-001'),
        name: 'gene-regulation-mechanisms',
        type: 'papers'
    },
    { 
        source: path.join(BASE_PATH, 'papers', 'neural-plasticity-modeling-002'),
        name: 'neural-plasticity-modeling',
        type: 'papers'
    },
    
    // Technical Design Documents
    { 
        source: path.join(BASE_PATH, 'technical_design_documents', 'agriculture-20250704-001'),
        name: 'agriculture-optimization',
        type: 'technical_design_documents'
    },
    { 
        source: path.join(BASE_PATH, 'technical_design_documents', 'biology-20250704-001'),
        name: 'biology-research',
        type: 'technical_design_documents'
    },
    { 
        source: path.join(BASE_PATH, 'technical_design_documents', 'chemistry-20250704-001'),
        name: 'chemistry-analysis',
        type: 'technical_design_documents'
    },
    { 
        source: path.join(BASE_PATH, 'technical_design_documents', 'computer-science-20250705-001'),
        name: 'computer-science-research',
        type: 'technical_design_documents'
    },
    { 
        source: path.join(BASE_PATH, 'technical_design_documents', 'energy-20250704-001'),
        name: 'energy-systems',
        type: 'technical_design_documents'
    },
    { 
        source: path.join(BASE_PATH, 'technical_design_documents', 'environmental-science-20250704-001'),
        name: 'environmental-science',
        type: 'technical_design_documents'
    },
    { 
        source: path.join(BASE_PATH, 'technical_design_documents', 'materials-science-20250705-001'),
        name: 'materials-science',
        type: 'technical_design_documents'
    },
    { 
        source: path.join(BASE_PATH, 'technical_design_documents', 'psychology-20250704-001'),
        name: 'psychology-research',
        type: 'technical_design_documents'
    },
    { 
        source: path.join(BASE_PATH, 'technical_design_documents', 'robotics-20250705-001'),
        name: 'robotics-systems',
        type: 'technical_design_documents'
    },
    
    // Implementation Plans
    { 
        source: path.join(BASE_PATH, 'implementation_plans', 'llmxive-automation-testing'),
        name: 'llmxive-automation-testing',
        type: 'implementation_plans'
    },
    
    // Reviews
    { 
        source: path.join(BASE_PATH, 'reviews', 'chemistry-20250704-001'),
        name: 'chemistry-review',
        type: 'reviews'
    },
    { 
        source: path.join(BASE_PATH, 'reviews', 'materials-science-20250705-001'),
        name: 'materials-science-review',
        type: 'reviews'
    },
    
    // Code
    { 
        source: path.join(BASE_PATH, 'code', 'llmxive-automation'),
        name: 'llmxive-automation',
        type: 'code'
    }
];

// Track migrated projects
const migratedProjects = [];

// Execute migrations
migrations.forEach(migration => {
    if (fs.existsSync(migration.source)) {
        const projectId = migrateProject(migration.source, migration.name, migration.type);
        migratedProjects.push({
            id: projectId,
            name: migration.name,
            source: migration.source,
            type: migration.type
        });
    } else {
        console.log(`Source not found: ${migration.source}`);
    }
});

// Create migration report
const report = {
    timestamp: new Date().toISOString(),
    total_migrated: migratedProjects.length,
    projects: migratedProjects,
    next_counter: projectCounter
};

fs.writeFileSync(
    path.join(BASE_PATH, 'migration-report-phase2.json'),
    JSON.stringify(report, null, 2)
);

console.log(`Migration completed! Migrated ${migratedProjects.length} projects.`);
console.log(`Report saved to: migration-report-phase2.json`);
console.log(`Next project counter: ${projectCounter}`);

// Print summary
console.log('\n=== MIGRATION SUMMARY ===');
migratedProjects.forEach(project => {
    console.log(`✓ ${project.id} (${project.name}) from ${project.type}`);
});