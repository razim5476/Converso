

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from channels.auth import AuthMiddlewareStack


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'a_core.settings')

django_asgi_app = get_asgi_application()

# Import routing modules from a_rtc and a_videocall
from a_rtchat.routing import websocket_urlpatterns as rtc_routing
from a_videocall.routing import websocket_urlpatterns as videocall_routing

# Combine all routing
websocket_urlpatterns = rtc_routing + videocall_routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    )
})
