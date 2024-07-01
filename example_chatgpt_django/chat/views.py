import json
import uuid


from django.conf import settings

from channels.generic.websocket import WebsocketConsumer

from django.template.loader import render_to_string
from django.views.generic import TemplateView
from openai import OpenAI


class ChatView(TemplateView):
    template_name = "chat.html"


def _format_token(token: str) -> str:
    # apply very basic formatting while we're rendering tokens in real-time
    token = token.replace("\n", "<br>")
    return token


class ChatConsumerDemo(WebsocketConsumer):
    def connect(self):
        print("connect")
        self.messages = []

        self.accept()

    def disconnect(self, close_code):
        print("disconnect")
        pass

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_text = text_data_json["message"]

        # do nothing with empty messages
        if not message_text.strip():
            return

        # add to messages
        self.messages.append(
            {
                "role": "user",
                "content": message_text,
            }
        )

        # show user's message
        user_message_html = render_to_string(
            "chat/user_message_demo.html",
            {
                "message_text": message_text,
            },
        )
        self.send(text_data=user_message_html)

        # render an empty system message where we'll stream our response
        message_id = uuid.uuid4().hex
        contents_div_id = f"message-response-{message_id}"
        system_message_html = render_to_string(
            "chat/system_message.html",
            {
                "contents_div_id": contents_div_id,
            },
        )
        self.send(text_data=system_message_html)

        # call chatgpt api
        client = OpenAI(api_key=settings.OPENAI_APIKEY)
        openai_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=self.messages,
            stream=True,
        )

        chunks = []
        for chunk in openai_response:
            message_chunk = chunk.choices[0].delta.content
            if message_chunk:
                chunks.append(message_chunk)
                # use htmx to insert the next token at the end of our system message.
                chunk = f'<div hx-swap-oob="beforeend:#{contents_div_id}">{_format_token(message_chunk)}</div>'
                self.send(text_data=chunk)
            print(chunk)
        system_message = "".join(chunks)
        # replace final input with fully rendered version, so we can render markdown, etc.
        final_message_html = render_to_string(
            "chat/final_system_message_demo.html",
            {
                "contents_div_id": contents_div_id,
                "message": system_message,
            },
        )
        # add to messages
        self.messages.append(
            {
                "role": "system",
                "content": system_message,
            }
        )

        self.send(text_data=final_message_html)
