# call/consumers.py
import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

class CallConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        
        # Notify the client that the connection was successful
        self.send(text_data=json.dumps({
            'type': 'connection',
            'data': {
                'message': "Connected"
            }
        }))

    def disconnect(self, close_code):
        # Leave room group when the connection closes
        async_to_sync(self.channel_layer.group_discard)(
            self.my_name,
            self.channel_name
        )

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        event_type = text_data_json['type']

        # Handle login
        if event_type == 'login':
            name = text_data_json['data']['name']
            self.my_name = name
            async_to_sync(self.channel_layer.group_add)(
                self.my_name,
                self.channel_name
            )

        # Handle incoming call
        if event_type == 'call':
            room_id = text_data_json['data']['room_id']
            self.my_name = text_data_json['data']['caller']

            # Send the call to the specified room (callee)
            async_to_sync(self.channel_layer.group_send)(
                room_id,
                {
                    'type': 'call_received',
                    'data': {
                        'caller': self.my_name,
                        'rtcMessage': text_data_json['data']['rtcMessage']
                    }
                }
            )

        # Handle call answer
        if event_type == 'answer_call':
            caller = text_data_json['data']['caller']
            async_to_sync(self.channel_layer.group_send)(
                caller,
                {
                    'type': 'call_answered',
                    'data': {
                        'rtcMessage': text_data_json['data']['rtcMessage']
                    }
                }
            )

        # Handle ICE candidate
        if event_type == 'ICEcandidate':
            user = text_data_json['data']['user']
            async_to_sync(self.channel_layer.group_send)(
                user,
                {
                    'type': 'ICEcandidate',
                    'data': {
                        'rtcMessage': text_data_json['data']['rtcMessage']
                    }
                }
            )

    # Handle receiving the call
    def call_received(self, event):
        self.send(text_data=json.dumps({
            'type': 'call_received',
            'data': event['data']
        }))

    # Handle answering the call
    def call_answered(self, event):
        self.send(text_data=json.dumps({
            'type': 'call_answered',
            'data': event['data']
        }))

    # Handle ICE candidates
    def ICEcandidate(self, event):
        self.send(text_data=json.dumps({
            'type': 'ICEcandidate',
            'data': event['data']
        }))
