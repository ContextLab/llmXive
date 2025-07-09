#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const BASE_PATH = '/Users/jmanning/llmXive';
const PROJECTS_PATH = path.join(BASE_PATH, 'projects');
const DATABASE_PATH = path.join(BASE_PATH, 'web/database/projects.json');

// Read database
const database = JSON.parse(fs.readFileSync(DATABASE_PATH, 'utf8'));

// Project counter starting after the highest existing number
let projectCounter = 1;

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

console.log(`Starting standardization with counter: ${projectCounter}`);

// Define naming mappings for projects that need to be renamed
const namingMappings = [
    // Test projects to be renamed
    { old: 'CLI-TEST-2', new: `PROJ-${String(projectCounter++).padStart(3, '0')}-cli-test-2` },
    { old: 'PDF-TEST', new: `PROJ-${String(projectCounter++).padStart(3, '0')}-pdf-test` },
    { old: 'TEST-E2E-complete', new: `PROJ-${String(projectCounter++).padStart(3, '0')}-e2e-test-complete` },
    
    // Old date-based projects to be renamed
    { old: 'PROJ-20250704-agriculture-20250704-001', new: `PROJ-${String(projectCounter++).padStart(3, '0')}-agriculture-systems` },
    { old: 'PROJ-20250704-biology-20250704-001', new: `PROJ-${String(projectCounter++).padStart(3, '0')}-biology-gene-regulation` },
    { old: 'PROJ-20250704-chemistry-20250704-001', new: `PROJ-${String(projectCounter++).padStart(3, '0')}-chemistry-renewable-energy` },
    { old: 'PROJ-20250704-energy-20250704-001', new: `PROJ-${String(projectCounter++).padStart(3, '0')}-energy-equity` },
    { old: 'PROJ-20250704-environmental-science-20250704-001', new: `PROJ-${String(projectCounter++).padStart(3, '0')}-environmental-monitoring` },
    { old: 'PROJ-20250704-psychology-20250704-001', new: `PROJ-${String(projectCounter++).padStart(3, '0')}-psychology-digital-health` },
    { old: 'PROJ-20250705-computer-science-20250705-001', new: `PROJ-${String(projectCounter++).padStart(3, '0')}-computer-science-accessibility` },
    { old: 'PROJ-20250705-materials-science-20250705-001', new: `PROJ-${String(projectCounter++).padStart(3, '0')}-materials-science-fuel-cells` },
    { old: 'PROJ-20250705-robotics-20250705-001', new: `PROJ-${String(projectCounter++).padStart(3, '0')}-robotics-autonomous-systems` },
    
    // Duplicates to be renamed
    { old: 'PROJ-001-gene-regulation-mechanisms-001', new: `PROJ-${String(projectCounter++).padStart(3, '0')}-gene-regulation-ctcf` },
    { old: 'PROJ-002-neural-plasticity-modeling-002', new: `PROJ-${String(projectCounter++).padStart(3, '0')}-neural-plasticity-modeling` },
    { old: 'PROJ-20250706-gene-regulation-mechanisms', new: `PROJ-${String(projectCounter++).padStart(3, '0')}-gene-regulation-alt` },
    
    // Fix naming for automation projects
    { old: 'PROJ-001-automated-pipeline-scheduler', new: `PROJ-${String(projectCounter++).padStart(3, '0')}-automated-pipeline-scheduler` },
    { old: 'PROJ-001-llmxive-automation-testing', new: `PROJ-${String(projectCounter++).padStart(3, '0')}-llmxive-automation-testing` },
    { old: 'PROJ-001-llmxive-automation', new: `PROJ-${String(projectCounter++).padStart(3, '0')}-llmxive-automation` }
];

// Track renames
const renames = [];

// Execute renames
namingMappings.forEach(mapping => {
    const oldPath = path.join(PROJECTS_PATH, mapping.old);
    const newPath = path.join(PROJECTS_PATH, mapping.new);
    
    if (fs.existsSync(oldPath)) {
        console.log(`Renaming: ${mapping.old} -> ${mapping.new}`);
        
        // Rename directory
        fs.renameSync(oldPath, newPath);
        
        // Update config file if it exists
        const configPath = path.join(newPath, '.llmxive', 'config.json');
        if (fs.existsSync(configPath)) {
            const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
            config.id = mapping.new;
            config.renamed = true;
            config.oldId = mapping.old;
            fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
        }
        
        renames.push(mapping);
    } else {
        console.log(`Source not found: ${mapping.old}`);
    }
});

// Update database with new names
database.projects.forEach(project => {
    const rename = renames.find(r => r.old === project.id);
    if (rename) {
        project.id = rename.new;
        project.location = `projects/${rename.new}/`;
        project.dateModified = new Date().toISOString();
        console.log(`Updated database entry: ${rename.old} -> ${rename.new}`);
    }
});

// Update metadata
database.metadata.version = "2.2.0";
database.metadata.description = "llmXive Projects Database - Standardized naming convention";
database.metadata.lastUpdated = new Date().toISOString();

// Write updated database
fs.writeFileSync(DATABASE_PATH, JSON.stringify(database, null, 2));

// Create rename report
const report = {
    timestamp: new Date().toISOString(),
    total_renamed: renames.length,
    next_counter: projectCounter,
    renames: renames
};

fs.writeFileSync(
    path.join(BASE_PATH, 'naming-standardization-report.json'),
    JSON.stringify(report, null, 2)
);

console.log(`\\n=== STANDARDIZATION COMPLETE ===`);
console.log(`Total projects renamed: ${renames.length}`);
console.log(`Next project counter: ${projectCounter}`);
console.log(`Database updated with ${database.projects.length} projects`);

// Print summary
console.log('\\n=== RENAMED PROJECTS ===');
renames.forEach(rename => {
    console.log(`✓ ${rename.old} -> ${rename.new}`);
});