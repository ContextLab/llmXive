/**
 * Utility functions and classes for llmXive
 * Common helpers, formatters, and shared functionality
 */

/**
 * Notification Manager
 * Handles toast notifications and alerts
 */
export class NotificationManager {
    constructor() {
        this.container = null;
        this.notifications = new Map();
        this.defaultDuration = 5000;
        this.maxNotifications = 5;
        
        this.init();
    }
    
    init() {
        this.container = document.getElementById('notifications-container');
        if (!this.container) {
            this.createContainer();
        }
    }
    
    createContainer() {
        this.container = document.createElement('div');
        this.container.id = 'notifications-container';
        this.container.className = 'notifications-container';
        document.body.appendChild(this.container);
    }
    
    show(message, type = 'info', options = {}) {
        const id = Math.random().toString(36).substr(2, 9);
        const duration = options.duration || this.defaultDuration;
        const persistent = options.persistent || false;
        const actions = options.actions || [];
        
        // Limit number of notifications
        if (this.notifications.size >= this.maxNotifications) {
            const oldestId = this.notifications.keys().next().value;
            this.hide(oldestId);
        }
        
        const notification = this.createNotification(id, message, type, actions);
        this.container.appendChild(notification);
        this.notifications.set(id, notification);
        
        // Trigger show animation
        requestAnimationFrame(() => {
            notification.classList.add('show');
        });
        
        // Auto-hide after duration
        if (!persistent && duration > 0) {
            setTimeout(() => {
                this.hide(id);
            }, duration);
        }
        
        return id;
    }
    
    createNotification(id, message, type, actions) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.dataset.id = id;
        
        const header = document.createElement('div');
        header.className = 'notification-header';
        
        const title = document.createElement('h4');
        title.className = 'notification-title';
        title.textContent = this.getTitleForType(type);
        
        const closeBtn = document.createElement('button');
        closeBtn.className = 'notification-close';
        closeBtn.innerHTML = '<i class="fas fa-times"></i>';
        closeBtn.addEventListener('click', () => this.hide(id));
        
        header.appendChild(title);
        header.appendChild(closeBtn);
        
        const body = document.createElement('div');
        body.className = 'notification-body';
        body.textContent = message;
        
        notification.appendChild(header);
        notification.appendChild(body);
        
        // Add action buttons if provided
        if (actions.length > 0) {
            const actionsContainer = document.createElement('div');
            actionsContainer.className = 'notification-actions';
            
            actions.forEach(action => {
                const button = document.createElement('button');
                button.className = `btn btn-sm ${action.style || 'btn-secondary'}`;
                button.textContent = action.label;
                button.addEventListener('click', () => {
                    if (action.handler) action.handler();
                    if (action.dismiss !== false) this.hide(id);
                });
                actionsContainer.appendChild(button);
            });
            
            notification.appendChild(actionsContainer);
        }
        
        return notification;
    }
    
    getTitleForType(type) {
        const titles = {
            success: 'Success',
            error: 'Error',
            warning: 'Warning',
            info: 'Information'
        };
        return titles[type] || 'Notification';
    }
    
    hide(id) {
        const notification = this.notifications.get(id);
        if (!notification) return;
        
        notification.classList.remove('show');
        notification.classList.add('hide');
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
            this.notifications.delete(id);
        }, 300);
    }
    
    clear() {
        Array.from(this.notifications.keys()).forEach(id => {
            this.hide(id);
        });
    }
    
    success(message, options = {}) {
        return this.show(message, 'success', options);
    }
    
    error(message, options = {}) {
        return this.show(message, 'error', { ...options, duration: 0 });
    }
    
    warning(message, options = {}) {
        return this.show(message, 'warning', options);
    }
    
    info(message, options = {}) {
        return this.show(message, 'info', options);
    }
}

/**
 * Date and time utilities
 */
export class DateUtils {
    static formatRelative(date) {
        const now = new Date();
        const diff = now - new Date(date);
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);
        
        if (seconds < 60) return 'just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        
        return new Date(date).toLocaleDateString();
    }
    
    static formatDateTime(date) {
        return new Date(date).toLocaleString();
    }
    
    static formatDate(date) {
        return new Date(date).toLocaleDateString();
    }
    
    static formatTime(date) {
        return new Date(date).toLocaleTimeString();
    }
    
    static isToday(date) {
        const today = new Date();
        const checkDate = new Date(date);
        return today.toDateString() === checkDate.toDateString();
    }
    
    static isWithinDays(date, days) {
        const now = new Date();
        const checkDate = new Date(date);
        const diffTime = Math.abs(now - checkDate);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        return diffDays <= days;
    }
}

/**
 * String utilities
 */
export class StringUtils {
    static truncate(str, length = 100, suffix = '...') {
        if (str.length <= length) return str;
        return str.substring(0, length) + suffix;
    }
    
    static capitalize(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }
    
    static camelCase(str) {
        return str.replace(/(?:^\w|[A-Z]|\b\w)/g, (word, index) => {
            return index === 0 ? word.toLowerCase() : word.toUpperCase();
        }).replace(/\s+/g, '');
    }
    
    static kebabCase(str) {
        return str
            .replace(/([a-z])([A-Z])/g, '$1-$2')
            .replace(/\s+/g, '-')
            .toLowerCase();
    }
    
    static slugify(str) {
        return str
            .toLowerCase()
            .replace(/[^\w\s-]/g, '')
            .replace(/[\s_-]+/g, '-')
            .replace(/^-+|-+$/g, '');
    }
    
    static stripHtml(str) {
        const div = document.createElement('div');
        div.innerHTML = str;
        return div.textContent || div.innerText || '';
    }
    
    static highlight(text, query) {
        if (!query) return text;
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }
}

/**
 * Number utilities
 */
export class NumberUtils {
    static formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
        
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }
    
    static formatNumber(num, decimals = 0) {
        return num.toLocaleString(undefined, {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
    }
    
    static formatPercentage(value, total, decimals = 1) {
        if (total === 0) return '0%';
        const percentage = (value / total) * 100;
        return `${percentage.toFixed(decimals)}%`;
    }
    
    static clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }
    
    static randomBetween(min, max) {
        return Math.random() * (max - min) + min;
    }
}

/**
 * DOM utilities
 */
export class DOMUtils {
    static createElement(tag, className = '', content = '') {
        const element = document.createElement(tag);
        if (className) element.className = className;
        if (content) element.textContent = content;
        return element;
    }
    
    static createIcon(iconClass) {
        const icon = document.createElement('i');
        icon.className = iconClass;
        return icon;
    }
    
    static empty(element) {
        while (element.firstChild) {
            element.removeChild(element.firstChild);
        }
    }
    
    static show(element) {
        element.style.display = '';
        element.classList.remove('hidden');
    }
    
    static hide(element) {
        element.style.display = 'none';
        element.classList.add('hidden');
    }
    
    static toggle(element) {
        if (element.style.display === 'none' || element.classList.contains('hidden')) {
            this.show(element);
        } else {
            this.hide(element);
        }
    }
    
    static isVisible(element) {
        return element.offsetParent !== null;
    }
    
    static scrollToTop(element = window, smooth = true) {
        if (element === window) {
            window.scrollTo({
                top: 0,
                behavior: smooth ? 'smooth' : 'auto'
            });
        } else {
            element.scrollTo({
                top: 0,
                behavior: smooth ? 'smooth' : 'auto'
            });
        }
    }
    
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    static throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
}

/**
 * Local storage utilities
 */
export class StorageUtils {
    static set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('Error saving to localStorage:', error);
            return false;
        }
    }
    
    static get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('Error reading from localStorage:', error);
            return defaultValue;
        }
    }
    
    static remove(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('Error removing from localStorage:', error);
            return false;
        }
    }
    
    static clear() {
        try {
            localStorage.clear();
            return true;
        } catch (error) {
            console.error('Error clearing localStorage:', error);
            return false;
        }
    }
    
    static has(key) {
        return localStorage.getItem(key) !== null;
    }
    
    static size() {
        return localStorage.length;
    }
}

/**
 * URL utilities
 */
export class URLUtils {
    static getParams() {
        return new URLSearchParams(window.location.search);
    }
    
    static getParam(name, defaultValue = null) {
        const params = this.getParams();
        return params.get(name) || defaultValue;
    }
    
    static setParam(name, value) {
        const url = new URL(window.location);
        url.searchParams.set(name, value);
        window.history.replaceState({}, '', url);
    }
    
    static removeParam(name) {
        const url = new URL(window.location);
        url.searchParams.delete(name);
        window.history.replaceState({}, '', url);
    }
    
    static updateParams(params) {
        const url = new URL(window.location);
        Object.entries(params).forEach(([key, value]) => {
            if (value === null || value === undefined) {
                url.searchParams.delete(key);
            } else {
                url.searchParams.set(key, value);
            }
        });
        window.history.replaceState({}, '', url);
    }
}

/**
 * Validation utilities
 */
export class ValidationUtils {
    static isEmail(email) {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regex.test(email);
    }
    
    static isUrl(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    }
    
    static isRequired(value) {
        return value !== null && value !== undefined && value.toString().trim() !== '';
    }
    
    static minLength(value, length) {
        return value && value.toString().length >= length;
    }
    
    static maxLength(value, length) {
        return !value || value.toString().length <= length;
    }
    
    static isNumber(value) {
        return !isNaN(parseFloat(value)) && isFinite(value);
    }
    
    static isInteger(value) {
        return Number.isInteger(Number(value));
    }
    
    static inRange(value, min, max) {
        const num = Number(value);
        return num >= min && num <= max;
    }
}

/**
 * Error handling utilities
 */
export class ErrorUtils {
    static handle(error, context = '') {
        console.error(`Error${context ? ` in ${context}` : ''}:`, error);
        
        // Extract meaningful error message
        let message = 'An unexpected error occurred';
        
        if (error.message) {
            message = error.message;
        } else if (typeof error === 'string') {
            message = error;
        }
        
        return {
            message,
            context,
            originalError: error,
            timestamp: new Date().toISOString()
        };
    }
    
    static async withRetry(fn, maxAttempts = 3, delay = 1000) {
        let lastError;
        
        for (let attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                return await fn();
            } catch (error) {
                lastError = error;
                
                if (attempt === maxAttempts) {
                    throw error;
                }
                
                // Wait before retrying
                await new Promise(resolve => setTimeout(resolve, delay * attempt));
            }
        }
        
        throw lastError;
    }
    
    static isNetworkError(error) {
        return error.name === 'NetworkError' || 
               error.message.includes('fetch') ||
               error.message.includes('network');
    }
    
    static isAuthError(error) {
        return error.status === 401 || 
               error.status === 403 ||
               error.message.includes('authentication') ||
               error.message.includes('unauthorized');
    }
}

/**
 * Color utilities
 */
export class ColorUtils {
    static hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : null;
    }
    
    static rgbToHex(r, g, b) {
        return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
    }
    
    static getContrast(hex) {
        const rgb = this.hexToRgb(hex);
        if (!rgb) return '#000000';
        
        const brightness = (rgb.r * 299 + rgb.g * 587 + rgb.b * 114) / 1000;
        return brightness > 128 ? '#000000' : '#ffffff';
    }
    
    static lighten(hex, amount) {
        const rgb = this.hexToRgb(hex);
        if (!rgb) return hex;
        
        return this.rgbToHex(
            Math.min(255, Math.floor(rgb.r + (255 - rgb.r) * amount)),
            Math.min(255, Math.floor(rgb.g + (255 - rgb.g) * amount)),
            Math.min(255, Math.floor(rgb.b + (255 - rgb.b) * amount))
        );
    }
    
    static darken(hex, amount) {
        const rgb = this.hexToRgb(hex);
        if (!rgb) return hex;
        
        return this.rgbToHex(
            Math.max(0, Math.floor(rgb.r * (1 - amount))),
            Math.max(0, Math.floor(rgb.g * (1 - amount))),
            Math.max(0, Math.floor(rgb.b * (1 - amount)))
        );
    }
}

/**
 * Performance utilities
 */
export class PerformanceUtils {
    static measure(name, fn) {
        const start = performance.now();
        const result = fn();
        const end = performance.now();
        console.log(`${name} took ${end - start} milliseconds`);
        return result;
    }
    
    static async measureAsync(name, fn) {
        const start = performance.now();
        const result = await fn();
        const end = performance.now();
        console.log(`${name} took ${end - start} milliseconds`);
        return result;
    }
    
    static createObserver(callback, options = {}) {
        if ('IntersectionObserver' in window) {
            return new IntersectionObserver(callback, {
                threshold: 0.1,
                rootMargin: '50px',
                ...options
            });
        }
        return null;
    }
    
    static lazy(fn, delay = 0) {
        return new Promise(resolve => {
            setTimeout(() => resolve(fn()), delay);
        });
    }
}

// Export all utilities as default
export default {
    NotificationManager,
    DateUtils,
    StringUtils,
    NumberUtils,
    DOMUtils,
    StorageUtils,
    URLUtils,
    ValidationUtils,
    ErrorUtils,
    ColorUtils,
    PerformanceUtils
};