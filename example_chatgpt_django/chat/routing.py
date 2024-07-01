# routing.py
from django.urls import path

from .views import ChatConsumerDemo

websocket_urlpatterns = [path(r"ws/chat/", ChatConsumerDemo.as_asgi())]
