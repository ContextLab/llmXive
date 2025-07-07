/**
 * Jest setup file for llmXive tests
 */

// Mock localStorage
Object.defineProperty(window, 'localStorage', {
    value: {
        getItem: jest.fn(),
        setItem: jest.fn(),
        removeItem: jest.fn(),
        clear: jest.fn(),
    },
    writable: true,
});

// Mock sessionStorage
Object.defineProperty(window, 'sessionStorage', {
    value: {
        getItem: jest.fn(),
        setItem: jest.fn(),
        removeItem: jest.fn(),
        clear: jest.fn(),
    },
    writable: true,
});

// Mock fetch
global.fetch = jest.fn();

// Mock crypto.getRandomValues
Object.defineProperty(global, 'crypto', {
    value: {
        getRandomValues: jest.fn(() => new Uint8Array(32)),
        subtle: {
            digest: jest.fn(() => Promise.resolve(new ArrayBuffer(32))),
        },
    },
});

// Mock btoa/atob
global.btoa = jest.fn((str) => Buffer.from(str).toString('base64'));
global.atob = jest.fn((str) => Buffer.from(str, 'base64').toString());

// Mock GitHub API responses
export const mockGitHubResponses = {
    user: {
        login: 'testuser',
        id: 12345,
        name: 'Test User',
        avatar_url: 'https://github.com/avatar.jpg',
    },
    repo: {
        id: 123456,
        name: 'llmXive',
        full_name: 'ContextLab/llmXive',
        permissions: {
            admin: false,
            push: true,
            pull: true,
        },
    },
    file: {
        type: 'file',
        content: btoa(JSON.stringify({ test: 'data' })),
        sha: 'abc123def456',
    },
    createFile: {
        content: {
            sha: 'def456abc789',
            path: 'test/file.json',
        },
        commit: {
            sha: 'ghi789jkl012',
            message: 'Test commit',
        },
    },
};

// Reset mocks before each test
beforeEach(() => {
    jest.clearAllMocks();
    localStorage.getItem.mockReturnValue(null);
    sessionStorage.getItem.mockReturnValue(null);
    
    // Reset fetch mock
    fetch.mockClear();
    fetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockGitHubResponses.user),
    });
});

// Global test utilities
global.testUtils = {
    createMockGitHubClient: () => ({
        rest: {
            repos: {
                getContent: jest.fn(() => Promise.resolve({ data: mockGitHubResponses.file })),
                createOrUpdateFileContents: jest.fn(() => Promise.resolve({ data: mockGitHubResponses.createFile })),
            },
        },
    }),
    
    createMockFileManager: () => ({
        readJSON: jest.fn(() => Promise.resolve({ test: 'data' })),
        writeJSON: jest.fn(() => Promise.resolve()),
        appendToLog: jest.fn(() => Promise.resolve()),
        fileExists: jest.fn(() => Promise.resolve(true)),
        createDirectory: jest.fn(() => Promise.resolve()),
        getStats: jest.fn(() => ({ memoryCacheSize: 0, queueLength: 0 })),
    }),
    
    createMockSystemConfig: () => ({
        initialize: jest.fn(() => Promise.resolve()),
        isInitialized: jest.fn(() => Promise.resolve(true)),
        loadConfig: jest.fn(() => Promise.resolve({})),
        loadRegistries: jest.fn(() => Promise.resolve({})),
        getStatus: jest.fn(() => Promise.resolve({})),
    }),
    
    sleep: (ms) => new Promise(resolve => setTimeout(resolve, ms)),
};