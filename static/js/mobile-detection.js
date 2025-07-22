/**
 * Mobile device detection and optimization utilities
 */

class MobileDetection {
    constructor() {
        this.isMobile = this.detectMobile();
        this.isTablet = this.detectTablet();
        this.isIOS = this.detectIOS();
        this.isAndroid = this.detectAndroid();
        this.hasCamera = false; // Will be set async
        
        this.init();
        this.detectCamera().then(hasCamera => {
            this.hasCamera = hasCamera;
        }).catch(() => {
            this.hasCamera = false;
        });
    }
    
    detectMobile() {
        const userAgent = navigator.userAgent || navigator.vendor || window.opera;
        
        // Check for mobile patterns
        const mobileRegex = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i;
        const isMobileUA = mobileRegex.test(userAgent);
        
        // Check for touch support
        const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
        
        // Check screen size
        const isSmallScreen = window.innerWidth <= 768 || window.screen.width <= 768;
        
        return isMobileUA || (hasTouch && isSmallScreen);
    }
    
    detectTablet() {
        const userAgent = navigator.userAgent;
        return /iPad|Android/i.test(userAgent) && window.innerWidth >= 768;
    }
    
    async detectCamera() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            return false;
        }
        
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            return devices.some(device => device.kind === 'videoinput');
        } catch (error) {
            console.warn('Camera detection failed:', error);
            return false;
        }
    }
    
    detectIOS() {
        return /iPad|iPhone|iPod/.test(navigator.userAgent) || 
               (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    }
    
    detectAndroid() {
        return /Android/.test(navigator.userAgent);
    }
    
    init() {
        // Add device classes to body
        document.body.classList.toggle('mobile-device', this.isMobile);
        document.body.classList.toggle('tablet-device', this.isTablet);
        document.body.classList.toggle('ios-device', this.isIOS);
        document.body.classList.toggle('android-device', this.isAndroid);
        
        // Initialize mobile optimizations
        if (this.isMobile) {
            this.initMobileOptimizations();
        }
    }
    
    initMobileOptimizations() {
        // Disable zoom on form inputs (iOS)
        if (this.isIOS) {
            this.preventIOSZoom();
        }
        
        // Optimize touch interactions
        this.optimizeTouchInteractions();
        
        // Add mobile-specific event listeners
        this.addMobileEventListeners();
        
        // Optimize viewport for mobile
        this.optimizeViewport();
    }
    
    preventIOSZoom() {
        // Prevent zoom on input focus in iOS
        const inputs = document.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            if (input.style.fontSize === '' || parseInt(input.style.fontSize) < 16) {
                input.style.fontSize = '16px';
            }
        });
    }
    
    optimizeTouchInteractions() {
        // Add touch-friendly button sizing
        const buttons = document.querySelectorAll('.btn');
        buttons.forEach(button => {
            if (this.isMobile && !button.classList.contains('btn-sm')) {
                button.classList.add('mobile-touch-target');
            }
        });
        
        // Improve link tap targets
        const links = document.querySelectorAll('a');
        links.forEach(link => {
            link.style.minHeight = '44px';
            link.style.minWidth = '44px';
        });
    }
    
    addMobileEventListeners() {
        // Handle orientation changes
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                this.handleOrientationChange();
            }, 100);
        });
        
        // Handle viewport changes
        window.addEventListener('resize', () => {
            this.handleViewportChange();
        });
        
        // Optimize scroll performance
        this.optimizeScrollPerformance();
    }
    
    handleOrientationChange() {
        // Trigger camera layout adjustment if camera is active
        if (window.cameraCapture && window.cameraCapture.isCapturing) {
            window.cameraCapture.adjustCameraLayout();
        }
        
        // Adjust modal heights
        this.adjustModalHeights();
        
        // Dispatch custom event
        window.dispatchEvent(new CustomEvent('mobileOrientationChange', {
            detail: { orientation: screen.orientation?.angle || 0 }
        }));
    }
    
    handleViewportChange() {
        // Update mobile detection if viewport changes significantly
        const wasMobile = this.isMobile;
        this.isMobile = this.detectMobile();
        
        if (wasMobile !== this.isMobile) {
            document.body.classList.toggle('mobile-device', this.isMobile);
        }
    }
    
    adjustModalHeights() {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            if (modal.classList.contains('show')) {
                // Force re-calculation of modal height
                const modalBody = modal.querySelector('.modal-body');
                if (modalBody) {
                    modalBody.style.height = 'auto';
                    modalBody.style.maxHeight = '80vh';
                }
            }
        });
    }
    
    optimizeScrollPerformance() {
        // Use passive event listeners for touch events
        const passiveOptions = { passive: true };
        
        document.addEventListener('touchstart', () => {}, passiveOptions);
        document.addEventListener('touchmove', () => {}, passiveOptions);
        document.addEventListener('touchend', () => {}, passiveOptions);
    }
    
    optimizeViewport() {
        // Set appropriate viewport meta tag
        let viewport = document.querySelector('meta[name="viewport"]');
        if (!viewport) {
            viewport = document.createElement('meta');
            viewport.name = 'viewport';
            document.head.appendChild(viewport);
        }
        
        if (this.isMobile) {
            viewport.content = 'width=device-width, initial-scale=1.0, user-scalable=no, viewport-fit=cover';
        } else {
            viewport.content = 'width=device-width, initial-scale=1.0';
        }
    }
    
    // Utility methods
    showMobileAlert(message, type = 'info') {
        // Mobile-optimized alert display
        const alert = document.createElement('div');
        alert.className = `mobile-alert alert-${type}`;
        alert.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 9999;
            padding: 12px 20px;
            border-radius: 8px;
            background: ${type === 'error' ? '#dc3545' : type === 'success' ? '#198754' : '#0dcaf0'};
            color: white;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            max-width: 90vw;
            text-align: center;
        `;
        
        alert.innerHTML = message;
        document.body.appendChild(alert);
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateX(-50%) translateY(-20px)';
            setTimeout(() => alert.remove(), 300);
        }, 3000);
    }
    
    requestCameraPermission() {
        // Request camera permission with mobile-friendly messaging
        if (!this.hasCamera) {
            this.showMobileAlert('Camera not available on this device', 'error');
            return Promise.reject('No camera');
        }
        
        return navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                // Stop the stream immediately - we just wanted to test permission
                stream.getTracks().forEach(track => track.stop());
                return true;
            })
            .catch(error => {
                let message = 'Camera permission denied';
                
                if (error.name === 'NotAllowedError') {
                    message = 'Please allow camera access in your browser settings';
                } else if (error.name === 'NotFoundError') {
                    message = 'No camera found on this device';
                } else if (error.name === 'NotReadableError') {
                    message = 'Camera is in use by another application';
                }
                
                this.showMobileAlert(message, 'error');
                throw error;
            });
    }
    
    // Public API
    getDeviceInfo() {
        return {
            isMobile: this.isMobile,
            isTablet: this.isTablet,
            hasCamera: this.hasCamera,
            isIOS: this.isIOS,
            isAndroid: this.isAndroid,
            userAgent: navigator.userAgent,
            viewport: {
                width: window.innerWidth,
                height: window.innerHeight
            }
        };
    }
}

// Initialize mobile detection when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.mobileDetection = new MobileDetection();
    
    // Log device info for debugging
    console.log('Device Info:', window.mobileDetection.getDeviceInfo());
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MobileDetection;
}