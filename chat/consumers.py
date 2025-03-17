import json
import redis
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

redis_client = redis.Redis(host='localhost', port=6379, db=0)

class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sender_id = None
        self.sender = None
        self.receiver_id = None
        self.receiver = None
        self.chat = None
        self.chat_name = None

    async def connect(self):

        self.sender_id = self.scope['user'].id
        self.sender = self.scope['user']
        self.receiver_id = self.scope['url_route']['kwargs']['receiver_id']
        self.receiver = await self.get_user(self.receiver_id)
        self.chat = await self.get_or_create_chat(self.sender, self.receiver)
        self.chat_name = f"chat_{min(self.sender_id, self.receiver_id)}_{max(self.sender_id, self.receiver_id)}"

        redis_client.set(self.sender_id, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        redis_client.delete(self.sender_id)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['content']

        # Save the message to the database
        message_obj = await self.create_message(self.chat, self.sender, self.receiver, message)
        timestamp_str = message_obj.timestamp.strftime("%B %d, %Y, %I:%M %p").replace(" 0", " ").lower().replace("am", "a.m.").replace("pm", "p.m.")

        # Check if the receiver is online
        receiver_channel_name = redis_client.get(self.receiver_id)
        if receiver_channel_name:
            # Send the message to the receiver
            await self.channel_layer.send(
                receiver_channel_name.decode('utf-8'),  
                {
                    'type': 'handle_incoming_message',
                    'message': message,
                    'timestamp': timestamp_str,
                }
            )
        else:
            # Send an email to the receiver
            pass

        # Send the message back to the sender
        html_message = (
            f'<div hx-swap-oob="beforeend:#messages">'
            f'<div class="message sent">'
            f'<div class="content">'
            f'<div class="text">{message}</div>'
            f'<div class="timestamp">{timestamp_str}</div>'
            f'</div>'
            f'</div>'
            f'</div>'
        )

        await self.send(text_data=html_message)


    async def handle_incoming_message(self, event):
        message = event['message']
        timestamp = event['timestamp']
        html_message = (
            f'<div hx-swap-oob="beforeend:#messages">'
            f'<div class="message received">'
            f'<div class="content">'
            f'<div class="text">{message}</div>'
            f'<div class="timestamp">{timestamp}</div>'
            f'</div>'
            f'</div>'
            f'</div>'
        )

        await self.send(text_data=html_message)


    @sync_to_async
    def get_user(self, user_id):
        from django.contrib.auth.models import User
        return User.objects.get(id=user_id)

    @sync_to_async
    def get_or_create_chat(self, sender, receiver):
        from .models import Chat
        chat = Chat.objects.filter(participants=sender).filter(participants=receiver).first()
        if not chat:
            chat = Chat.objects.create()
            chat.participants.set([sender, receiver])
        return chat


    @sync_to_async
    def create_message(self, chat, sender, receiver, content):
        from .models import Message
        return Message.objects.create(chat=chat, sender=sender, receiver=receiver, content=content)

