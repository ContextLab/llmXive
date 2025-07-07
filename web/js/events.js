/**
 * Event system for llmXive web interface
 * Simple EventTarget polyfill and event utilities
 */

/**
 * EventTarget polyfill for better browser compatibility
 */
export class EventTarget {
    constructor() {
        this.listeners = new Map();
    }
    
    addEventListener(type, listener, options = {}) {
        if (!this.listeners.has(type)) {
            this.listeners.set(type, new Set());
        }
        
        const listenerObj = {
            listener,
            once: options.once || false
        };
        
        this.listeners.get(type).add(listenerObj);
    }
    
    removeEventListener(type, listener) {
        if (!this.listeners.has(type)) return;
        
        const typeListeners = this.listeners.get(type);
        for (const listenerObj of typeListeners) {
            if (listenerObj.listener === listener) {
                typeListeners.delete(listenerObj);
                break;
            }
        }
        
        if (typeListeners.size === 0) {
            this.listeners.delete(type);
        }
    }
    
    dispatchEvent(event) {
        const type = event.type || event;
        
        if (!this.listeners.has(type)) return true;
        
        const typeListeners = this.listeners.get(type);
        const listenersToRemove = [];
        
        for (const listenerObj of typeListeners) {
            try {
                if (typeof event === 'string') {
                    listenerObj.listener();
                } else {
                    listenerObj.listener(event);
                }
                
                if (listenerObj.once) {
                    listenersToRemove.push(listenerObj);
                }
            } catch (error) {
                console.error('Error in event listener:', error);
            }
        }
        
        // Remove one-time listeners
        listenersToRemove.forEach(listenerObj => {
            typeListeners.delete(listenerObj);
        });
        
        return true;
    }
    
    // Convenience methods
    on(type, listener, options) {
        this.addEventListener(type, listener, options);
    }
    
    off(type, listener) {
        this.removeEventListener(type, listener);
    }
    
    emit(type, data) {
        const event = typeof type === 'string' ? { type, data } : type;
        this.dispatchEvent(event);
    }
    
    once(type, listener) {
        this.addEventListener(type, listener, { once: true });
    }
}

/**
 * Event utilities
 */
export class EventUtils {
    /**
     * Create a custom event
     */
    static createEvent(type, data = {}, options = {}) {
        const event = new CustomEvent(type, {
            detail: data,
            bubbles: options.bubbles || false,
            cancelable: options.cancelable || false
        });
        
        return event;
    }
    
    /**
     * Dispatch a custom event on an element
     */
    static dispatch(element, type, data = {}, options = {}) {
        const event = this.createEvent(type, data, options);
        element.dispatchEvent(event);
        return event;
    }
    
    /**
     * Add event listener with automatic cleanup
     */
    static listen(element, type, listener, options = {}) {
        element.addEventListener(type, listener, options);
        
        return () => {
            element.removeEventListener(type, listener, options);
        };
    }
    
    /**
     * Add multiple event listeners
     */
    static listenMultiple(element, events, listener, options = {}) {
        const cleanupFunctions = events.map(event => 
            this.listen(element, event, listener, options)
        );
        
        return () => {
            cleanupFunctions.forEach(cleanup => cleanup());
        };
    }
    
    /**
     * Wait for an event to occur
     */
    static waitFor(element, type, timeout = 5000) {
        return new Promise((resolve, reject) => {
            let timeoutId;
            
            const cleanup = this.listen(element, type, (event) => {
                if (timeoutId) clearTimeout(timeoutId);
                cleanup();
                resolve(event);
            });
            
            if (timeout > 0) {
                timeoutId = setTimeout(() => {
                    cleanup();
                    reject(new Error(`Event '${type}' did not occur within ${timeout}ms`));
                }, timeout);
            }
        });
    }
    
    /**
     * Debounce event handler
     */
    static debounce(handler, delay = 300) {
        let timeoutId;
        
        return function(...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => handler.apply(this, args), delay);
        };
    }
    
    /**
     * Throttle event handler
     */
    static throttle(handler, limit = 100) {
        let inThrottle;
        
        return function(...args) {
            if (!inThrottle) {
                handler.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
    
    /**
     * Prevent default and stop propagation
     */
    static prevent(event) {
        event.preventDefault();
        event.stopPropagation();
        return false;
    }
    
    /**
     * Check if event target matches selector
     */
    static matches(event, selector) {
        return event.target.matches && event.target.matches(selector);
    }
    
    /**
     * Find closest element matching selector
     */
    static closest(event, selector) {
        return event.target.closest && event.target.closest(selector);
    }
    
    /**
     * Delegate event handling
     */
    static delegate(parent, selector, type, handler) {
        return this.listen(parent, type, (event) => {
            const target = this.closest(event, selector);
            if (target) {
                handler.call(target, event);
            }
        });
    }
}

/**
 * Event emitter for pub/sub pattern
 */
export class EventEmitter extends EventTarget {
    constructor() {
        super();
        this.maxListeners = 10;
    }
    
    setMaxListeners(n) {
        this.maxListeners = n;
        return this;
    }
    
    getMaxListeners() {
        return this.maxListeners;
    }
    
    listenerCount(type) {
        return this.listeners.has(type) ? this.listeners.get(type).size : 0;
    }
    
    eventNames() {
        return Array.from(this.listeners.keys());
    }
    
    removeAllListeners(type) {
        if (type) {
            this.listeners.delete(type);
        } else {
            this.listeners.clear();
        }
        return this;
    }
    
    prependListener(type, listener) {
        // Add to beginning (approximate since Set doesn't have prepend)
        this.addEventListener(type, listener);
        return this;
    }
    
    prependOnceListener(type, listener) {
        this.addEventListener(type, listener, { once: true });
        return this;
    }
}

/**
 * Global event bus for application-wide communication
 */
export class EventBus extends EventEmitter {
    constructor() {
        super();
        this.setMaxListeners(50); // Higher limit for global bus
    }
    
    /**
     * Emit event with namespace support
     */
    emitNamespaced(namespace, event, data) {
        this.emit(`${namespace}:${event}`, data);
        this.emit(event, data); // Also emit without namespace
    }
    
    /**
     * Listen to namespaced events
     */
    onNamespaced(namespace, event, listener) {
        this.on(`${namespace}:${event}`, listener);
    }
    
    /**
     * Remove namespaced listeners
     */
    offNamespaced(namespace, event, listener) {
        this.off(`${namespace}:${event}`, listener);
    }
    
    /**
     * Remove all listeners for a namespace
     */
    offNamespace(namespace) {
        const pattern = new RegExp(`^${namespace}:`);
        const eventNames = this.eventNames();
        
        eventNames.forEach(eventName => {
            if (pattern.test(eventName)) {
                this.removeAllListeners(eventName);
            }
        });
    }
}

// Create global event bus instance
export const eventBus = new EventBus();

/**
 * Event constants
 */
export const EVENTS = {
    // Authentication events
    AUTH_STATE_CHANGE: 'auth:stateChange',
    AUTH_LOGIN: 'auth:login',
    AUTH_LOGOUT: 'auth:logout',
    AUTH_ERROR: 'auth:error',
    
    // Navigation events
    NAV_CHANGE: 'nav:change',
    PAGE_LOAD: 'page:load',
    PAGE_UNLOAD: 'page:unload',
    
    // Data events
    DATA_LOAD: 'data:load',
    DATA_ERROR: 'data:error',
    DATA_UPDATE: 'data:update',
    DATA_DELETE: 'data:delete',
    
    // UI events
    UI_LOADING: 'ui:loading',
    UI_ERROR: 'ui:error',
    UI_SUCCESS: 'ui:success',
    UI_MODAL_OPEN: 'ui:modalOpen',
    UI_MODAL_CLOSE: 'ui:modalClose',
    
    // Project events
    PROJECT_CREATE: 'project:create',
    PROJECT_UPDATE: 'project:update',
    PROJECT_DELETE: 'project:delete',
    PROJECT_SELECT: 'project:select',
    
    // Review events
    REVIEW_CREATE: 'review:create',
    REVIEW_UPDATE: 'review:update',
    REVIEW_DELETE: 'review:delete',
    REVIEW_APPROVE: 'review:approve',
    REVIEW_REJECT: 'review:reject',
    
    // System events
    SYSTEM_READY: 'system:ready',
    SYSTEM_ERROR: 'system:error',
    SYSTEM_OFFLINE: 'system:offline',
    SYSTEM_ONLINE: 'system:online'
};

export default {
    EventTarget,
    EventUtils,
    EventEmitter,
    EventBus,
    eventBus,
    EVENTS
};