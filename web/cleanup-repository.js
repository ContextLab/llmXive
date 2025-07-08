#!/usr/bin/env node

/**
 * Repository Cleanup and Organization Script
 * 
 * This script will:
 * 1. Find all misplaced documents
 * 2. Move them to proper locations based on project IDs
 * 3. Update database entries to match actual file locations
 * 4. Create missing directories as needed
 * 5. Validate all links point to actual files
 */

const fs = require('fs');
const path = require('path');

console.log('🧹 Starting repository cleanup and organization...\n');

// Load project database
let projectsData;
try {
    projectsData = JSON.parse(fs.readFileSync('database/projects.json', 'utf8'));
} catch (error) {
    console.error('❌ Failed to load projects database:', error.message);
    process.exit(1);
}

const projects = projectsData.projects;
const changes = [];

// Create directory if it doesn't exist
function ensureDir(dirPath) {
    if (!fs.existsSync(dirPath)) {
        fs.mkdirSync(dirPath, { recursive: true });
        console.log(`📁 Created directory: ${dirPath}`);
    }
}

// Move file to new location
function moveFile(oldPath, newPath) {
    try {
        ensureDir(path.dirname(newPath));
        fs.renameSync(oldPath, newPath);
        console.log(`📄 Moved: ${oldPath} → ${newPath}`);
        return true;
    } catch (error) {
        console.error(`❌ Failed to move ${oldPath} to ${newPath}:`, error.message);
        return false;
    }
}

// Function to find files recursively
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

console.log('📋 Analyzing current file organization...\n');

// 1. Move misplaced files in web/ directory to proper locations
const webDocs = findFiles('./technical_design_documents', /\.md$/);
const misplacedInWeb = webDocs.filter(file => file.includes('/web/'));

console.log(`Found ${misplacedInWeb.length} files in web/ subdirectories:`);
misplacedInWeb.forEach(file => {
    console.log(`  - ${file}`);
    
    // Extract project info from path
    const relativePath = file.replace('./technical_design_documents/', '');
    const parts = relativePath.split('/');
    
    if (parts.length >= 3 && parts[1] === 'web') {
        // Move from technical_design_documents/projectId/web/file.md 
        // to technical_design_documents/projectId/file.md
        const projectId = parts[0];
        const fileName = parts[parts.length - 1];
        const newPath = `./technical_design_documents/${projectId}/${fileName}`;
        
        if (moveFile(file, newPath)) {
            changes.push({
                type: 'file_moved',
                from: file,
                to: newPath,
                project: projectId
            });
        }
    }
});

// 2. For each project, ensure proper directory structure and file locations
console.log('\n📁 Organizing project directories...\n');

Object.entries(projects).forEach(([projectId, project]) => {
    console.log(`🔍 Processing project: ${projectId}`);
    console.log(`   Title: ${project.title}`);
    
    // Create expected directory structure
    const expectedDirs = [
        `technical_design_documents/${projectId}`,
        `implementation_plans/${projectId}`,
        `papers/${projectId}`,
        `code/${projectId}`,
        `data/${projectId}`,
        `reviews/${projectId}/Design`,
        `reviews/${projectId}/Implementation`,
        `reviews/${projectId}/Paper`,
        `reviews/${projectId}/Code`
    ];
    
    expectedDirs.forEach(dir => {
        ensureDir(dir);
    });
    
    // Check current location in database
    const currentLocation = project.location;
    console.log(`   Current location: ${currentLocation || 'None specified'}`);
    
    // Look for actual design documents
    const possibleDesignPaths = [
        `technical_design_documents/${projectId}/design.md`,
        `technical_design_documents/${projectId}/design-completed.md`
    ];
    
    let actualDesignPath = null;
    for (const designPath of possibleDesignPaths) {
        if (fs.existsSync(designPath)) {
            actualDesignPath = designPath;
            console.log(`   ✅ Found design document: ${designPath}`);
            break;
        }
    }
    
    // Update database location if needed
    let newLocation = actualDesignPath;
    
    // If no design document exists locally, it should point to GitHub
    if (!actualDesignPath) {
        // Default to expected GitHub location
        newLocation = `technical_design_documents/${projectId}/design.md`;
        console.log(`   📝 No local document found, will reference GitHub: ${newLocation}`);
    }
    
    // Update database if location changed
    if (currentLocation !== newLocation) {
        console.log(`   🔄 Updating database location: ${currentLocation} → ${newLocation}`);
        project.location = newLocation;
        changes.push({
            type: 'database_updated',
            project: projectId,
            field: 'location',
            from: currentLocation,
            to: newLocation
        });
    }
    
    // Check and update review file locations
    if (project.reviews) {
        project.reviews.forEach(review => {
            if (review.location) {
                const reviewPath = review.location;
                console.log(`   📋 Review: ${reviewPath}`);
                
                // Ensure review directory exists
                ensureDir(path.dirname(reviewPath));
                
                // Check if review file exists
                if (!fs.existsSync(reviewPath)) {
                    console.log(`   ⚠️  Review file missing: ${reviewPath}`);
                }
            }
        });
    }
    
    console.log('');
});

// 3. Update the projects database
console.log('💾 Updating projects database...\n');

// Write updated database
try {
    const updatedJson = JSON.stringify(projectsData, null, 2);
    fs.writeFileSync('database/projects.json', updatedJson);
    console.log('✅ Updated database/projects.json');
} catch (error) {
    console.error('❌ Failed to update database:', error.message);
}

// 4. Clean up empty directories
console.log('\n🧹 Cleaning up empty directories...\n');

function removeEmptyDirs(dir) {
    if (!fs.existsSync(dir)) return;
    
    const files = fs.readdirSync(dir);
    if (files.length === 0) {
        fs.rmdirSync(dir);
        console.log(`🗑️  Removed empty directory: ${dir}`);
        return;
    }
    
    // Recursively check subdirectories
    files.forEach(file => {
        const fullPath = path.join(dir, file);
        if (fs.statSync(fullPath).isDirectory()) {
            removeEmptyDirs(fullPath);
        }
    });
    
    // Check again if directory is now empty
    const remainingFiles = fs.readdirSync(dir);
    if (remainingFiles.length === 0) {
        fs.rmdirSync(dir);
        console.log(`🗑️  Removed empty directory: ${dir}`);
    }
}

// Clean up potential empty web directories
findFiles('./technical_design_documents', /.*/).forEach(item => {
    if (fs.statSync(item).isDirectory() && item.includes('/web')) {
        removeEmptyDirs(item);
    }
});

// 5. Generate final report
console.log('\n' + '='.repeat(60));
console.log('📊 CLEANUP REPORT');
console.log('='.repeat(60));

console.log(`\n✅ COMPLETED ACTIONS (${changes.length}):`);
changes.forEach((change, index) => {
    console.log(`\n${index + 1}. ${change.type}`);
    if (change.project) {
        console.log(`   Project: ${change.project}`);
    }
    if (change.from && change.to) {
        console.log(`   ${change.from} → ${change.to}`);
    }
    if (change.field) {
        console.log(`   Field: ${change.field}`);
    }
});

// 6. Verify final state
console.log('\n🔍 FINAL VERIFICATION:');
Object.entries(projects).forEach(([projectId, project]) => {
    const location = project.location;
    const exists = location && fs.existsSync(location);
    const symbol = exists ? '✅' : '📋';
    const note = exists ? 'Local file' : 'GitHub reference';
    console.log(`   ${symbol} ${projectId}: ${location} (${note})`);
});

console.log('\n✅ Repository cleanup completed!');
console.log('\n📋 NEXT STEPS:');
console.log('   1. Review the changes above');
console.log('   2. Test document links in the web interface');
console.log('   3. Commit the reorganized files to Git');
console.log('   4. Update DocumentViewer to fetch from GitHub for missing files');
