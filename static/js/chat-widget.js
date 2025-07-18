/**
 * Chat Widget JavaScript
 * Floating chat assistant with easy access
 */

class ChatWidget {
    constructor() {
        this.isOpen = false;
        this.currentConversationId = null;
        this.chatbotConfig = null;
        this.messageQueue = [];
        this.isTyping = false;
        
        this.init();
    }
    
    async init() {
        // Check if user is logged in and chat is available
        if (!this.isUserLoggedIn()) {
            return;
        }
        
        // Load chatbot configuration
        await this.loadChatbotConfig();
        
        if (!this.chatbotConfig) {
            return;
        }
        
        this.createWidget();
        this.bindEvents();
    }
    
    isUserLoggedIn() {
        // Check if user session exists (look for user dropdown in nav)
        return document.querySelector('.navbar-nav .dropdown-toggle') !== null;
    }
    
    async loadChatbotConfig() {
        try {
            // In a real implementation, this would be an API call
            // For now, we'll use data attributes or inline config
            const configElement = document.getElementById('chatbot-config');
            if (configElement) {
                this.chatbotConfig = JSON.parse(configElement.textContent);
            } else {
                // Default configuration
                this.chatbotConfig = {
                    name: 'Okra Assistant',
                    greeting: 'Hello! I\'m here to help you with okra plant health questions.',
                    isAvailable: true
                };
            }
        } catch (error) {
            console.error('Failed to load chatbot config:', error);
        }
    }
    
    createWidget() {
        const widget = document.createElement('div');
        widget.className = 'chat-widget';
        widget.innerHTML = `
            <div class="chat-window" id="chatWindow">
                <div class="chat-header">
                    <div class="chat-avatar">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="chat-info">
                        <div class="chat-name">${this.chatbotConfig.name}</div>
                        <div class="chat-status">Online</div>
                    </div>
                    <button class="chat-close" id="chatClose">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                
                <div class="limited-mode-warning" id="limitedWarning" style="display: none;">
                    <i class="fas fa-exclamation-triangle me-1"></i>
                    Running in limited mode - some features may be unavailable
                </div>
                
                <div class="chat-messages" id="chatMessages">
                    <div class="message bot">
                        <div class="message-avatar">
                            <i class="fas fa-robot"></i>
                        </div>
                        <div class="message-content">
                            ${this.chatbotConfig.greeting}
                        </div>
                    </div>
                </div>
                
                <div class="chat-input">
                    <div class="chat-input-wrapper">
                        <textarea 
                            id="chatInput" 
                            placeholder="Type your message..." 
                            rows="1"
                            maxlength="500"></textarea>
                        <button class="chat-send" id="chatSend">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    </div>
                </div>
            </div>
            
            <button class="chat-button" id="chatButton">
                <i class="fas fa-comments"></i>
                <div class="chat-notification" id="chatNotification" style="display: none;">1</div>
            </button>
        `;
        
        document.body.appendChild(widget);
        
        // Auto-resize textarea
        this.setupTextareaResize();
    }
    
    bindEvents() {
        const chatButton = document.getElementById('chatButton');
        const chatClose = document.getElementById('chatClose');
        const chatWindow = document.getElementById('chatWindow');
        const chatInput = document.getElementById('chatInput');
        const chatSend = document.getElementById('chatSend');
        
        // Toggle chat window
        chatButton.addEventListener('click', () => this.toggleChat());
        chatClose.addEventListener('click', () => this.closeChat());
        
        // Send message
        chatSend.addEventListener('click', () => this.sendMessage());
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Close on outside click
        document.addEventListener('click', (e) => {
            if (this.isOpen && !chatWindow.contains(e.target) && !chatButton.contains(e.target)) {
                this.closeChat();
            }
        });
        
        // Prevent close when clicking inside chat
        chatWindow.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }
    
    setupTextareaResize() {
        const textarea = document.getElementById('chatInput');
        textarea.addEventListener('input', () => {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 80) + 'px';
        });
    }
    
    toggleChat() {
        if (this.isOpen) {
            this.closeChat();
        } else {
            this.openChat();
        }
    }
    
    openChat() {
        const chatWindow = document.getElementById('chatWindow');
        const chatButton = document.getElementById('chatButton');
        const chatInput = document.getElementById('chatInput');
        const notification = document.getElementById('chatNotification');
        
        chatWindow.classList.add('show');
        chatButton.innerHTML = '<i class="fas fa-minus"></i>';
        chatButton.classList.add('minimized');
        notification.style.display = 'none';
        
        this.isOpen = true;
        
        // Focus input after animation
        setTimeout(() => {
            chatInput.focus();
        }, 300);
        
        // Load conversation history if needed
        this.loadRecentConversation();
    }
    
    closeChat() {
        const chatWindow = document.getElementById('chatWindow');
        const chatButton = document.getElementById('chatButton');
        
        chatWindow.classList.remove('show');
        chatButton.innerHTML = '<i class="fas fa-comments"></i>';
        chatButton.classList.remove('minimized');
        
        this.isOpen = false;
    }
    
    async sendMessage() {
        const chatInput = document.getElementById('chatInput');
        const message = chatInput.value.trim();
        
        if (!message) return;
        
        // Add user message to chat
        this.addMessage('user', message);
        chatInput.value = '';
        chatInput.style.height = 'auto';
        
        // Show typing indicator
        this.showTypingIndicator();
        
        // Disable input
        this.setInputState(false);
        
        try {
            // Send message to server
            const response = await fetch('/chat/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    conversation_id: this.currentConversationId
                })
            });
            
            const data = await response.json();
            
            // Hide typing indicator
            this.hideTypingIndicator();
            
            if (data.success) {
                // Set conversation ID if new conversation
                if (!this.currentConversationId) {
                    this.currentConversationId = data.conversation_id;
                }
                
                // Add bot response
                this.addMessage('bot', data.bot_response);
                
                // Show warning if not using OpenAI
                if (!data.openai_success) {
                    this.showLimitedModeWarning();
                }
            } else {
                this.addMessage('system', 'Sorry, I encountered an error. Please try again.');
                this.showError(data.error || 'Failed to send message');
            }
        } catch (error) {
            console.error('Chat error:', error);
            this.hideTypingIndicator();
            this.addMessage('system', 'Network error. Please check your connection and try again.');
        } finally {
            // Re-enable input
            this.setInputState(true);
        }
    }
    
    addMessage(type, content, timestamp = null) {
        const messagesContainer = document.getElementById('chatMessages');
        const messageElement = document.createElement('div');
        
        const time = timestamp || new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        let avatarIcon, avatarClass;
        switch(type) {
            case 'user':
                avatarIcon = 'fa-user';
                avatarClass = 'user';
                break;
            case 'system':
                avatarIcon = 'fa-exclamation-triangle';
                avatarClass = 'bot';
                break;
            default:
                avatarIcon = 'fa-robot';
                avatarClass = 'bot';
        }
        
        messageElement.className = `message ${avatarClass}`;
        messageElement.innerHTML = `
            <div class="message-avatar">
                <i class="fas ${avatarIcon}"></i>
            </div>
            <div class="message-content">
                ${this.escapeHtml(content)}
                <div class="message-time">${time}</div>
            </div>
        `;
        
        messagesContainer.appendChild(messageElement);
        this.scrollToBottom();
    }
    
    showTypingIndicator() {
        const messagesContainer = document.getElementById('chatMessages');
        const typingElement = document.createElement('div');
        typingElement.className = 'message bot typing-indicator-message';
        typingElement.id = 'typingIndicator';
        typingElement.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="typing-indicator">
                <div class="typing-dots">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        
        messagesContainer.appendChild(typingElement);
        this.scrollToBottom();
        this.isTyping = true;
    }
    
    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
        this.isTyping = false;
    }
    
    setInputState(enabled) {
        const chatInput = document.getElementById('chatInput');
        const chatSend = document.getElementById('chatSend');
        
        chatInput.disabled = !enabled;
        chatSend.disabled = !enabled;
        
        if (enabled) {
            chatInput.focus();
        }
    }
    
    showLimitedModeWarning() {
        const warning = document.getElementById('limitedWarning');
        warning.style.display = 'block';
        
        // Hide after 5 seconds
        setTimeout(() => {
            warning.style.display = 'none';
        }, 5000);
    }
    
    showError(message) {
        // Could show a toast or inline error message
        console.error('Chat widget error:', message);
    }
    
    async loadRecentConversation() {
        // Load the most recent conversation if available
        try {
            const response = await fetch('/chat/conversations');
            const data = await response.json();
            
            if (data.success && data.conversations.length > 0) {
                const recentConv = data.conversations[0];
                if (recentConv.message_count > 1) { // More than just the greeting
                    this.currentConversationId = recentConv.id;
                    await this.loadConversationMessages(recentConv.id);
                }
            }
        } catch (error) {
            console.error('Failed to load recent conversation:', error);
        }
    }
    
    async loadConversationMessages(conversationId) {
        try {
            const response = await fetch(`/chat/conversation/${conversationId}`);
            const data = await response.json();
            
            if (data.success) {
                const messagesContainer = document.getElementById('chatMessages');
                // Clear existing messages except the greeting
                const greeting = messagesContainer.querySelector('.message.bot');
                messagesContainer.innerHTML = '';
                if (greeting) {
                    messagesContainer.appendChild(greeting);
                }
                
                // Add conversation messages
                data.messages.forEach(msg => {
                    if (msg.message_type !== 'system') {
                        const timestamp = new Date(msg.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                        this.addMessage(msg.message_type, msg.content, timestamp);
                    }
                });
            }
        } catch (error) {
            console.error('Failed to load conversation messages:', error);
        }
    }
    
    scrollToBottom() {
        const messagesContainer = document.getElementById('chatMessages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    showNotification() {
        if (!this.isOpen) {
            const notification = document.getElementById('chatNotification');
            notification.style.display = 'flex';
        }
    }
}

// Initialize chat widget when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Small delay to ensure all other scripts are loaded
    setTimeout(() => {
        window.chatWidget = new ChatWidget();
    }, 100);
});

// Add some utility functions for external use
window.ChatWidgetAPI = {
    open: () => window.chatWidget?.openChat(),
    close: () => window.chatWidget?.closeChat(),
    sendMessage: (message) => {
        if (window.chatWidget) {
            const input = document.getElementById('chatInput');
            if (input) {
                input.value = message;
                window.chatWidget.sendMessage();
            }
        }
    }
};