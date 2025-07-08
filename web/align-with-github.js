#!/usr/bin/env node

/**
 * GitHub Repository Alignment Script
 * 
 * This script aligns the local database with the actual GitHub repository structure:
 * 1. Maps old directory names to new standardized names
 * 2. Updates database to reflect actual GitHub content
 * 3. Ensures DocumentViewer can find files correctly
 */

const fs = require('fs');
const https = require('https');

console.log('🔗 Aligning local database with GitHub repository...\n');

// Load current database
let projectsData;
try {
    projectsData = JSON.parse(fs.readFileSync('database/projects.json', 'utf8'));
} catch (error) {
    console.error('❌ Failed to load projects database:', error.message);
    process.exit(1);
}

// Fetch GitHub repository structure
function fetchGitHubContents(path = 'technical_design_documents') {
    return new Promise((resolve, reject) => {
        const url = `https://api.github.com/repos/ContextLab/llmXive/contents/${path}`;
        
        https.get(url, { headers: { 'User-Agent': 'llmXive-alignment-script' } }, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    resolve(JSON.parse(data));
                } catch (error) {
                    reject(error);
                }
            });
        }).on('error', reject);
    });
}

async function main() {
    try {
        console.log('📥 Fetching GitHub repository structure...');
        const githubContents = await fetchGitHubContents();
        
        // Extract directory names
        const githubDirs = githubContents
            .filter(item => item.type === 'dir')
            .map(item => item.name);
        
        console.log('📂 GitHub directories found:');
        githubDirs.forEach(dir => console.log(`   - ${dir}`));
        
        // Create mapping of old names to new standardized names
        const directoryMapping = {
            'llmXive_automation': 'llmxive-auto-001',
            // Add other mappings as needed
        };
        
        // Reverse mapping for database updates
        const projectToGitHubDir = {};
        Object.entries(directoryMapping).forEach(([oldName, newName]) => {
            projectToGitHubDir[newName] = oldName;
        });
        
        console.log('\n🔄 Directory name mappings:');
        Object.entries(directoryMapping).forEach(([oldName, newName]) => {
            console.log(`   ${oldName} → ${newName}`);
        });
        
        // Update project database locations
        const projects = projectsData.projects;
        const updates = [];
        
        Object.entries(projects).forEach(([projectId, project]) => {
            const currentLocation = project.location;
            
            if (currentLocation && currentLocation.includes('technical_design_documents')) {
                // Extract the directory name from current location
                const pathParts = currentLocation.split('/');
                const dirName = pathParts[1]; // technical_design_documents/[dirName]/file.md
                
                // Check if this directory exists in GitHub
                let githubDirName = dirName;
                
                // If project ID maps to a different GitHub directory name
                if (projectToGitHubDir[projectId]) {
                    githubDirName = projectToGitHubDir[projectId];
                }
                
                // If the current directory name doesn't exist in GitHub, try to find it
                if (!githubDirs.includes(githubDirName)) {
                    // Try to find a matching directory
                    const possibleMatches = githubDirs.filter(dir => 
                        dir.toLowerCase().includes(projectId.toLowerCase()) ||
                        projectId.toLowerCase().includes(dir.toLowerCase().replace(/_/g, '-'))
                    );
                    
                    if (possibleMatches.length === 1) {
                        githubDirName = possibleMatches[0];
                        console.log(`🔍 Found match: ${projectId} → ${githubDirName}`);
                    } else if (possibleMatches.length > 1) {
                        console.log(`⚠️  Multiple matches for ${projectId}: ${possibleMatches.join(', ')}`);
                        githubDirName = possibleMatches[0]; // Use first match
                    } else {
                        console.log(`❓ No GitHub directory found for ${projectId}, keeping current: ${dirName}`);
                    }
                }
                
                // Update location to point to actual GitHub directory
                const fileName = pathParts[pathParts.length - 1]; // Get the filename
                const newLocation = `technical_design_documents/${githubDirName}/${fileName}`;
                
                if (newLocation !== currentLocation) {
                    console.log(`📝 Updating ${projectId}: ${currentLocation} → ${newLocation}`);
                    project.location = newLocation;
                    updates.push({
                        projectId,
                        from: currentLocation,
                        to: newLocation,
                        githubDir: githubDirName
                    });
                }
            }
        });
        
        // Check for GitHub directories not in our database
        console.log('\n🔍 GitHub directories not in database:');
        const projectDirs = Object.values(projects)
            .map(p => p.location ? p.location.split('/')[1] : null)
            .filter(Boolean);
        
        const unmappedDirs = githubDirs.filter(dir => !projectDirs.includes(dir));
        unmappedDirs.forEach(dir => {
            console.log(`   📂 ${dir} (not in database)`);
        });
        
        if (unmappedDirs.length > 0) {
            console.log('\n💡 Consider adding these projects to the database or updating project IDs');
        }
        
        // Save updated database
        if (updates.length > 0) {
            console.log('\n💾 Saving updated database...');
            fs.writeFileSync('database/projects.json', JSON.stringify(projectsData, null, 2));
            console.log('✅ Database updated successfully');
        } else {
            console.log('\n✨ No updates needed - database already aligned');
        }
        
        // Generate updated DocumentViewer mapping
        console.log('\n📝 Generating updated DocumentViewer mapping...');
        
        const documentPaths = {};
        Object.entries(projects).forEach(([projectId, project]) => {
            if (project.location) {
                const docType = project.location.includes('implementation_plans') ? 'implementation' : 'design';
                documentPaths[projectId] = {
                    [docType]: project.location
                };
            }
        });
        
        const mappingCode = `// Auto-generated GitHub-aligned document mapping
// Generated on ${new Date().toISOString()}

export const GITHUB_ALIGNED_PATHS = ${JSON.stringify(documentPaths, null, 2)};

// GitHub base URLs
export const GITHUB_RAW_BASE = 'https://raw.githubusercontent.com/ContextLab/llmXive/main';
export const GITHUB_BLOB_BASE = 'https://github.com/ContextLab/llmXive/blob/main';

// Get document path for a project
export function getDocumentPath(projectId, documentType = 'design') {
    const project = GITHUB_ALIGNED_PATHS[projectId];
    return project ? project[documentType] : null;
}

// Get GitHub raw URL for direct content fetching
export function getGitHubRawUrl(filePath) {
    return \`\${GITHUB_RAW_BASE}/\${filePath}\`;
}

// Get GitHub blob URL for viewing
export function getGitHubBlobUrl(filePath) {
    return \`\${GITHUB_BLOB_BASE}/\${filePath}\`;
}
`;
        
        fs.writeFileSync('src/data/GitHubAlignedPaths.js', mappingCode);
        console.log('✅ Generated src/data/GitHubAlignedPaths.js');
        
        // Final report
        console.log('\n' + '='.repeat(60));
        console.log('📊 ALIGNMENT REPORT');
        console.log('='.repeat(60));
        
        console.log(`\n✅ UPDATES MADE (${updates.length}):`);
        updates.forEach((update, index) => {
            console.log(`\n${index + 1}. ${update.projectId}`);
            console.log(`   Database: ${update.from} → ${update.to}`);
            console.log(`   GitHub: ${update.githubDir}`);
        });
        
        console.log(`\n📊 SUMMARY:`);
        console.log(`   - GitHub directories: ${githubDirs.length}`);
        console.log(`   - Database projects: ${Object.keys(projects).length}`);
        console.log(`   - Alignments made: ${updates.length}`);
        console.log(`   - Unmapped GitHub dirs: ${unmappedDirs.length}`);
        
        console.log('\n✅ Repository alignment completed!');
        
    } catch (error) {
        console.error('❌ Alignment failed:', error.message);
        process.exit(1);
    }
}

main();