from starlette.requests import Request
import uvicorn
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import HTMLResponse
from starlette.routing import Route
from settings import HOST, PORT

from github import github_homepage

def homepage(request: Request):
    with open("./index.html", "r") as f:
        html = f.read()
    return HTMLResponse(html)

routes = [
    Route("/", endpoint=homepage),
    Route("/github", endpoint=github_homepage),
    Route("/github/callback", endpoint=github_homepage)
]

app = Starlette(debug=True, routes=routes, middleware=[Middleware(SessionMiddleware, secret_key="")])

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
