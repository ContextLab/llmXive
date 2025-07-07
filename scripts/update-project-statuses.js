#!/usr/bin/env node

/**
 * Update Project Statuses Script
 * 
 * This script runs in GitHub Actions to update project statuses
 * based on review points and phase advancement criteria.
 */

import fs from 'fs/promises';
import path from 'path';

console.log('Updating project statuses...');

async function updateProjectStatuses() {
    try {
        const projectsPath = '.llmxive-system/projects';
        
        // Check if projects directory exists
        try {
            await fs.access(projectsPath);
        } catch {
            console.log('No projects directory found');
            return;
        }
        
        // Read all project files
        const files = await fs.readdir(projectsPath);
        const projectFiles = files.filter(file => file.endsWith('.json'));
        
        console.log(`Found ${projectFiles.length} projects to check`);
        
        for (const file of projectFiles) {
            const projectPath = path.join(projectsPath, file);
            const projectData = JSON.parse(await fs.readFile(projectPath, 'utf8'));
            
            console.log(`Checking project: ${projectData.id || file}`);
            
            // TODO: Implement actual status update logic
            // This would check review points and update phases accordingly
            
            // Example status update
            if (projectData.status) {
                projectData.lastStatusUpdate = new Date().toISOString();
                await fs.writeFile(projectPath, JSON.stringify(projectData, null, 2));
            }
        }
        
        console.log('Project status updates completed');
        
    } catch (error) {
        console.error('Error updating project statuses:', error);
        process.exit(1);
    }
}

updateProjectStatuses();