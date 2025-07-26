"""
Chatbot utility module for managing OpenAI-powered chat interactions
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

DISABLE_OPENAI = os.getenv("DISABLE_OPENAI", "false").lower() == "true"

if DISABLE_OPENAI:
    logger.info("OpenAI integration is disabled via DISABLE_OPENAI flag.")
    OPENAI_AVAILABLE = False

if not OPENAI_AVAILABLE or not os.getenv("OPENAI_API_KEY"):
    logger.info(
        "OpenAI not available. If you want to enable it:\n"
        "- Install: pip install openai\n"
        "- Set environment variable: export OPENAI_API_KEY='your_key_here'\n"
        "Or set DISABLE_OPENAI=true to suppress this message."
    )

class ChatbotService:
    """Service for managing chatbot interactions with OpenAI"""
    
    def __init__(self):
        self.openai_client = None
        if OPENAI_AVAILABLE and os.environ.get('OPENAI_API_KEY'):
            try:
                self.openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.openai_client = None
    
    def is_available(self) -> bool:
        """Check if the chatbot service is available"""
        return self.openai_client is not None
    
    def generate_response(self, chatbot_config: Dict, conversation_history: List[Dict], user_message: str) -> Tuple[str, bool]:
        """
        Generate a response using OpenAI
        
        Args:
            chatbot_config: Configuration for the chatbot
            conversation_history: List of previous messages
            user_message: The user's current message
            
        Returns:
            Tuple of (response_text, success_flag)
        """
        if not self.is_available():
            return self._get_fallback_response(user_message), False
        
        try:
            # Build conversation context
            messages = self._build_conversation_context(chatbot_config, conversation_history, user_message)
            
            # Generate response using OpenAI
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=messages,
                max_tokens=500,
                temperature=self._get_temperature_from_tone(chatbot_config.get('response_tone', 'helpful')),
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            response_text = response.choices[0].message.content.strip()
            logger.info(f"Generated response for user message: {user_message[:50]}...")
            
            return response_text, True
            
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {e}")
            return self._get_fallback_response(user_message), False
    
    def _build_conversation_context(self, chatbot_config: Dict, conversation_history: List[Dict], user_message: str) -> List[Dict]:
        """Build the conversation context for OpenAI"""
        messages = []
        
        # Add system prompt
        system_prompt = chatbot_config.get('system_prompt', '')
        if system_prompt:
            # Enhance system prompt with okra-specific knowledge
            enhanced_prompt = f"""
{system_prompt}

You are an AI assistant specialized in okra plant health and disease management. You have access to the following knowledge:

OKRA DISEASES AND TREATMENTS:
1. Bacterial Blight: Causes water-soaked spots on leaves. Treatment: Remove infected parts, apply copper-based fungicides, improve air circulation.
2. Leaf Spot: Circular brown spots with yellow halos. Treatment: Remove affected leaves, apply fungicide, avoid overhead watering.
3. Mosaic Virus: Yellow mottled patterns on leaves. Treatment: Remove infected plants, control aphids, use virus-resistant varieties.
4. Powdery Mildew: White powdery coating on leaves. Treatment: Improve air circulation, apply sulfur-based fungicides, avoid overhead watering.

GENERAL OKRA CARE:
- Watering: Deep, infrequent watering at soil level
- Fertilization: Balanced fertilizer every 4-6 weeks
- Harvesting: Pick pods every 2-3 days when 2-4 inches long
- Common issues: Heat stress, nutrient deficiency, pest problems

Provide helpful, accurate information about okra plant care and disease management. If you're unsure about something, recommend consulting with local agricultural experts.
"""
            messages.append({"role": "system", "content": enhanced_prompt})
        
        # Add conversation history (limit to prevent context overflow)
        max_history = chatbot_config.get('max_conversation_length', 20)
        recent_history = conversation_history[-max_history:] if len(conversation_history) > max_history else conversation_history
        
        for msg in recent_history:
            if msg['message_type'] == 'user':
                messages.append({"role": "user", "content": msg['content']})
            elif msg['message_type'] == 'bot':
                messages.append({"role": "assistant", "content": msg['content']})
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def _get_temperature_from_tone(self, tone: str) -> float:
        """Convert response tone to OpenAI temperature setting"""
        tone_mapping = {
            'formal': 0.3,
            'helpful': 0.5,
            'friendly': 0.7,
            'technical': 0.2
        }
        return tone_mapping.get(tone, 0.5)
    
    def _get_fallback_response(self, user_message: str) -> str:
        """Generate a fallback response when OpenAI is not available"""
        fallback_responses = {
            'greeting': "Hello! I'm here to help you with okra plant health questions. However, I'm currently running in limited mode. Please contact an admin to enable full AI capabilities.",
            'disease': "I understand you're asking about plant diseases. In limited mode, I recommend checking the disease detection feature in our main application or consulting with local agricultural experts.",
            'care': "For okra plant care questions, I recommend consulting the comprehensive guides available in agricultural extension services or speaking with local farming experts.",
            'default': "I'm currently running in limited mode. For the best assistance with okra plant health, please use our disease detection feature or contact support to enable full AI capabilities."
        }
        
        # Simple keyword-based response selection
        message_lower = user_message.lower()
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'greetings']):
            return fallback_responses['greeting']
        elif any(word in message_lower for word in ['disease', 'infection', 'spot', 'blight', 'mildew']):
            return fallback_responses['disease']
        elif any(word in message_lower for word in ['care', 'water', 'fertilizer', 'harvest']):
            return fallback_responses['care']
        else:
            return fallback_responses['default']
    
    def generate_conversation_title(self, first_message: str) -> str:
        """Generate a title for the conversation based on the first message"""
        if not self.is_available():
            return f"Chat - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Generate a short, descriptive title (max 5 words) for a conversation that starts with the following message. Focus on the main topic or question."},
                    {"role": "user", "content": first_message}
                ],
                max_tokens=20,
                temperature=0.3
            )
            
            title = response.choices[0].message.content.strip()
            return title[:50]  # Limit title length
            
        except Exception as e:
            logger.error(f"Error generating conversation title: {e}")
            return f"Chat - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

# Global chatbot service instance
chatbot_service = ChatbotService()
