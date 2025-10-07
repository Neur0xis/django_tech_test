"""
WebSocket consumers for real-time prompt response streaming.
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from datetime import datetime

logger = logging.getLogger(__name__)


class PromptConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling real-time prompt responses.
    Each user connects to their own channel: ws/prompts/<username>/
    """

    async def connect(self):
        """
        Handle WebSocket connection.
        Join user-specific group and send confirmation message.
        """
        self.username = self.scope['url_route']['kwargs']['username']
        self.room_group_name = f"user_{self.username}"
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Accept the connection
        await self.accept()
        
        # Send connection confirmation
        await self.send(json.dumps({
            "type": "connection_established",
            "message": f"WebSocket connected for user {self.username}",
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        logger.info(f"WebSocket connected: user={self.username}, channel={self.channel_name}")

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.
        Leave user-specific group.
        """
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        logger.info(f"WebSocket disconnected: user={self.username}, close_code={close_code}")

    async def receive(self, text_data):
        """
        Handle messages received from WebSocket client.
        Echo back the data for testing purposes.
        """
        try:
            data = json.loads(text_data)
            logger.info(f"WebSocket received from user={self.username}: {data}")
            
            # Echo the received data back to the client
            await self.send(json.dumps({
                "type": "echo",
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }))
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received from user={self.username}: {e}")
            await self.send(json.dumps({
                "type": "error",
                "message": "Invalid JSON format",
                "timestamp": datetime.utcnow().isoformat()
            }))

    async def send_prompt_response(self, event):
        """
        Handle prompt_response events from channel layer.
        Send the prompt data to the WebSocket client.
        
        Args:
            event: Dict containing 'data' key with prompt information
        """
        # Send prompt response to WebSocket
        await self.send(json.dumps({
            "type": "prompt_response",
            "data": event["data"],
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        logger.info(f"Sent prompt response to user={self.username}, prompt_id={event['data'].get('id')}")

