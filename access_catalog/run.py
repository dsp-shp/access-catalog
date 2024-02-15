
from fastapi import Request
from fastapi.responses import RedirectResponse
from nicegui import app, Client, ui
from starlette.middleware.base import BaseHTTPMiddleware

def run() -> None:
    from .views import HOST, PORT, TITLE, FAVICON, home, login

    class AuthMiddleware(BaseHTTPMiddleware):
        """ Middleware that restricts access to service pages

        It redirects the user to the login page if they are not authenticated.

        """
        async def dispatch(self, request: Request, call_next):
            if not app.storage.user.get('authenticated', False):
                if request.url.path in Client.page_routes.values() and request.url.path not in {'/login'}:
                    app.storage.user['referrer_path'] = request.url.path  # remember where the user wanted to go
                    return RedirectResponse('/login')
            return await call_next(request)

    app.add_middleware(AuthMiddleware)

    ui.run(
        host=HOST,
        port=PORT,
        title=TITLE, 
        favicon=FAVICON,
        storage_secret='THIS_NEEDS_TO_BE_CHANGED'
    )

if __name__ in {"__main__", "__mp_main__"}:
    run()