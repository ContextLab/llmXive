/**
 * Test suite for FileManager
 */

import FileManager from '../../src/core/FileManager.js';

describe('FileManager', () => {
    let fileManager;
    let mockGitHubClient;

    beforeEach(() => {
        mockGitHubClient = testUtils.createMockGitHubClient();
        fileManager = new FileManager(mockGitHubClient, {
            owner: 'TestOrg',
            repo: 'TestRepo',
            branch: 'test-branch',
            cacheTimeout: 1000,
        });
    });

    describe('Constructor', () => {
        test('should initialize with correct default options', () => {
            const fm = new FileManager(mockGitHubClient);
            expect(fm.owner).toBe('ContextLab');
            expect(fm.repo).toBe('llmXive');
            expect(fm.branch).toBe('main');
        });

        test('should initialize with custom options', () => {
            expect(fileManager.owner).toBe('TestOrg');
            expect(fileManager.repo).toBe('TestRepo');
            expect(fileManager.branch).toBe('test-branch');
        });

        test('should initialize cache structures', () => {
            expect(fileManager.memoryCache).toBeInstanceOf(Map);
            expect(fileManager.requestQueue).toEqual([]);
            expect(fileManager.isProcessingQueue).toBe(false);
        });
    });

    describe('Cache Management', () => {
        test('should generate correct cache key', () => {
            const key = fileManager.getCacheKey('test/file.json');
            expect(key).toBe('TestOrg/TestRepo/test-branch/test/file.json');
        });

        test('should set and get from memory cache', () => {
            const testData = { test: 'data' };
            fileManager.setCache('test.json', testData, 5000);
            
            const cached = fileManager.getFromCache('test.json');
            expect(cached).toEqual({ data: testData, source: 'memory' });
        });

        test('should return null for expired cache', async () => {
            const testData = { test: 'data' };
            fileManager.setCache('test.json', testData, 1); // 1ms TTL
            
            await testUtils.sleep(10); // Wait for expiration
            
            const cached = fileManager.getFromCache('test.json');
            expect(cached).toBeNull();
        });

        test('should clear specific cache entry', () => {
            fileManager.setCache('test1.json', { test: 1 });
            fileManager.setCache('test2.json', { test: 2 });
            
            fileManager.clearCache('test1.json');
            
            expect(fileManager.getFromCache('test1.json')).toBeNull();
            expect(fileManager.getFromCache('test2.json')).not.toBeNull();
        });

        test('should clear all cache', () => {
            fileManager.setCache('test1.json', { test: 1 });
            fileManager.setCache('test2.json', { test: 2 });
            
            fileManager.clearCache();
            
            expect(fileManager.getFromCache('test1.json')).toBeNull();
            expect(fileManager.getFromCache('test2.json')).toBeNull();
        });
    });

    describe('readJSON', () => {
        test('should read JSON file successfully', async () => {
            const expectedData = { test: 'data' };
            mockGitHubClient.rest.repos.getContent.mockResolvedValue({
                data: {
                    type: 'file',
                    content: btoa(JSON.stringify(expectedData)),
                },
            });

            const result = await fileManager.readJSON('test.json');
            
            expect(result).toEqual(expectedData);
            expect(mockGitHubClient.rest.repos.getContent).toHaveBeenCalledWith({
                owner: 'TestOrg',
                repo: 'TestRepo',
                path: 'test.json',
                ref: 'test-branch',
            });
        });

        test('should return cached data when available', async () => {
            const cachedData = { cached: true };
            fileManager.setCache('test.json', cachedData);

            const result = await fileManager.readJSON('test.json');
            
            expect(result).toEqual(cachedData);
            expect(mockGitHubClient.rest.repos.getContent).not.toHaveBeenCalled();
        });

        test('should return null for 404 errors', async () => {
            const error = new Error('Not Found');
            error.status = 404;
            mockGitHubClient.rest.repos.getContent.mockRejectedValue(error);

            const result = await fileManager.readJSON('nonexistent.json');
            
            expect(result).toBeNull();
        });

        test('should throw error for non-404 errors', async () => {
            const error = new Error('Server Error');
            error.status = 500;
            mockGitHubClient.rest.repos.getContent.mockRejectedValue(error);

            await expect(fileManager.readJSON('test.json')).rejects.toThrow('Server Error');
        });

        test('should throw error for non-file content', async () => {
            mockGitHubClient.rest.repos.getContent.mockResolvedValue({
                data: { type: 'dir' },
            });

            await expect(fileManager.readJSON('test')).rejects.toThrow('Expected file but got dir');
        });
    });

    describe('writeJSON', () => {
        test('should write new JSON file successfully', async () => {
            const testData = { test: 'data' };
            mockGitHubClient.rest.repos.getContent.mockRejectedValue({ status: 404 });

            await fileManager.writeJSON('test.json', testData, 'Test commit');
            
            expect(mockGitHubClient.rest.repos.createOrUpdateFileContents).toHaveBeenCalledWith({
                owner: 'TestOrg',
                repo: 'TestRepo',
                path: 'test.json',
                message: 'Test commit',
                content: btoa(JSON.stringify(testData, null, 2)),
                branch: 'test-branch',
            });
        });

        test('should update existing JSON file successfully', async () => {
            const testData = { test: 'updated' };
            const existingSha = 'existing-sha-123';
            
            mockGitHubClient.rest.repos.getContent.mockResolvedValue({
                data: { sha: existingSha },
            });

            await fileManager.writeJSON('test.json', testData);
            
            expect(mockGitHubClient.rest.repos.createOrUpdateFileContents).toHaveBeenCalledWith({
                owner: 'TestOrg',
                repo: 'TestRepo',
                path: 'test.json',
                message: 'Update test.json',
                content: btoa(JSON.stringify(testData, null, 2)),
                branch: 'test-branch',
                sha: existingSha,
            });
        });

        test('should update cache after successful write', async () => {
            const testData = { test: 'data' };
            mockGitHubClient.rest.repos.getContent.mockRejectedValue({ status: 404 });

            await fileManager.writeJSON('test.json', testData);
            
            const cached = fileManager.getFromCache('test.json');
            expect(cached).toEqual({ data: testData, source: 'memory' });
        });
    });

    describe('appendToLog', () => {
        test('should append to new log file', async () => {
            const logEntry = { type: 'test', message: 'Test message' };
            
            // Mock empty log file
            fileManager.readJSON = jest.fn().mockResolvedValue(null);
            fileManager.writeJSON = jest.fn().mockResolvedValue();

            const result = await fileManager.appendToLog('test.log', logEntry);
            
            expect(result.type).toBe('test');
            expect(result.message).toBe('Test message');
            expect(result.timestamp).toBeDefined();
            
            expect(fileManager.writeJSON).toHaveBeenCalledWith(
                'test.log',
                expect.objectContaining({
                    entries: [expect.objectContaining(logEntry)],
                    created: expect.any(String),
                    lastUpdated: expect.any(String),
                }),
                'Append to log: test'
            );
        });

        test('should append to existing log file', async () => {
            const existingLog = {
                entries: [{ type: 'old', timestamp: '2023-01-01T00:00:00.000Z' }],
                created: '2023-01-01T00:00:00.000Z',
            };
            const newEntry = { type: 'new', message: 'New message' };
            
            fileManager.readJSON = jest.fn().mockResolvedValue(existingLog);
            fileManager.writeJSON = jest.fn().mockResolvedValue();

            await fileManager.appendToLog('test.log', newEntry);
            
            expect(fileManager.writeJSON).toHaveBeenCalledWith(
                'test.log',
                expect.objectContaining({
                    entries: expect.arrayContaining([
                        existingLog.entries[0],
                        expect.objectContaining(newEntry),
                    ]),
                }),
                'Append to log: new'
            );
        });

        test('should trim log when exceeding max size', async () => {
            const entries = Array.from({ length: 15 }, (_, i) => ({ 
                type: 'test', 
                index: i,
                timestamp: new Date().toISOString(),
            }));
            const existingLog = { entries, created: '2023-01-01T00:00:00.000Z' };
            
            fileManager.readJSON = jest.fn().mockResolvedValue(existingLog);
            fileManager.writeJSON = jest.fn().mockResolvedValue();

            await fileManager.appendToLog('test.log', { type: 'new' }, 10);
            
            const writeCall = fileManager.writeJSON.mock.calls[0][1];
            expect(writeCall.entries).toHaveLength(10);
            expect(writeCall.trimmed).toBe(6); // 15 existing + 1 new - 10 kept = 6 trimmed
        });
    });

    describe('Error Handling and Rate Limiting', () => {
        test('should handle consecutive errors with backoff', async () => {
            const error = new Error('API Error');
            mockGitHubClient.rest.repos.getContent.mockRejectedValue(error);

            // Trigger multiple consecutive errors
            for (let i = 0; i < 3; i++) {
                try {
                    await fileManager.readJSON(`test${i}.json`);
                } catch (e) {
                    // Expected to fail
                }
            }

            expect(fileManager.consecutiveErrors).toBe(3);
        });

        test('should reset error count on successful request', async () => {
            // Set up some errors first
            fileManager.consecutiveErrors = 3;
            
            // Mock successful response
            mockGitHubClient.rest.repos.getContent.mockResolvedValue({
                data: {
                    type: 'file',
                    content: btoa(JSON.stringify({ test: 'data' })),
                },
            });

            await fileManager.readJSON('test.json');
            
            expect(fileManager.consecutiveErrors).toBe(0);
        });
    });

    describe('Utility Methods', () => {
        test('fileExists should return true for existing file', async () => {
            mockGitHubClient.rest.repos.getContent.mockResolvedValue({ data: {} });

            const exists = await fileManager.fileExists('test.json');
            
            expect(exists).toBe(true);
        });

        test('fileExists should return false for non-existing file', async () => {
            const error = new Error('Not Found');
            error.status = 404;
            mockGitHubClient.rest.repos.getContent.mockRejectedValue(error);

            const exists = await fileManager.fileExists('nonexistent.json');
            
            expect(exists).toBe(false);
        });

        test('getStats should return current statistics', () => {
            fileManager.setCache('test1.json', { test: 1 });
            fileManager.setCache('test2.json', { test: 2 });
            fileManager.requestQueue.push({}, {});

            const stats = fileManager.getStats();
            
            expect(stats).toEqual({
                memoryCacheSize: 2,
                queueLength: 2,
                consecutiveErrors: 0,
                isProcessingQueue: false,
            });
        });
    });
});