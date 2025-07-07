#!/usr/bin/env node

/**
 * Generate Review Summary Script
 * 
 * This script generates a summary report of the automated review process
 * for display in GitHub Actions summary.
 */

import fs from 'fs/promises';
import path from 'path';

console.log('Generating review summary report...');

async function generateReviewSummary() {
    try {
        const logsPath = '.llmxive-system/logs';
        
        // Initialize summary data
        const summary = {
            timestamp: new Date().toISOString(),
            reviewsGenerated: 0,
            projectsUpdated: 0,
            tasksProcessed: 0,
            errors: []
        };
        
        // Check for completed tasks
        try {
            const completedTasksPath = path.join(logsPath, 'completed-tasks.json');
            const completedTasks = JSON.parse(await fs.readFile(completedTasksPath, 'utf8'));
            summary.tasksProcessed = completedTasks.length;
        } catch {
            // No completed tasks file
        }
        
        // Check for review logs
        try {
            const reviewLogsPath = path.join(logsPath, 'automated-reviews.json');
            const reviewLogs = JSON.parse(await fs.readFile(reviewLogsPath, 'utf8'));
            summary.reviewsGenerated = reviewLogs.length || 0;
        } catch {
            // No review logs file
        }
        
        // Generate markdown summary
        const markdownSummary = `
# 🤖 llmXive Automated Review Summary

**Generated:** ${new Date(summary.timestamp).toLocaleString()}

## 📊 Summary Statistics

- **Reviews Generated:** ${summary.reviewsGenerated}
- **Projects Updated:** ${summary.projectsUpdated}
- **Tasks Processed:** ${summary.tasksProcessed}

## 🔄 Process Status

${summary.tasksProcessed > 0 ? 
    `✅ Successfully processed ${summary.tasksProcessed} queued tasks` : 
    '⏸️ No tasks were queued for processing'}

${summary.reviewsGenerated > 0 ? 
    `✅ Generated ${summary.reviewsGenerated} automated reviews` : 
    '📝 No new reviews were generated'}

${summary.errors.length > 0 ? 
    `⚠️ Encountered ${summary.errors.length} errors during processing` : 
    '✅ No errors encountered'}

## 🔍 Next Steps

- Monitor project advancement based on review points
- Check for any projects ready for phase promotion
- Review any flagged content in moderation queue

---
*Automated by llmXive Review System*
        `.trim();
        
        console.log(markdownSummary);
        
    } catch (error) {
        console.error('Error generating review summary:', error);
        process.exit(1);
    }
}

generateReviewSummary();