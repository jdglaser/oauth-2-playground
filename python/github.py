import os
from typing import Optional
import requests
from starlette.requests import Request
from starlette.responses import Response, HTMLResponse, RedirectResponse
from urllib import parse
from settings import GITHUB_CLIENT_SECRET, GITHUB_CLIENT_ID, BASE_URL

AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
TOKEN_URL = "https://github.com/login/oauth/access_token"
API_URL_BASE = "https://api.github.com/"


async def handle_action(request: Request) -> Response:
    """
    Handles actions from the request.  Can be login, logout, or repos
    """
    params = request.query_params
    action = params.get("action")

    if action == "login":
        request.session["access_token"] = None
        generated_state = os.urandom(16).hex()

        request.session["state"] = generated_state

        github_query_params = {
            "response_type": "code",
            "client_id": GITHUB_CLIENT_ID,
            "redirect_uri": f"{BASE_URL}github/callback",
            "scope": "user public_repo",
            "state": generated_state
        }
        redirect_url = f"{AUTHORIZE_URL}?{parse.urlencode(github_query_params)}"
        return RedirectResponse(redirect_url)
    
    if action == "logout":
        request.session["access_token"] = None
        response = RedirectResponse(f"{BASE_URL}github")
        return response
    
    if action == "repos":
        result = await make_api_request(f"{API_URL_BASE}user/repos", request, "get", params={"sort": "created", "direction": "desc"})
        with open("./github/list_repos.html", "r") as f:
            repo_html = "\n".join([f"<li>{repo['name']}</li>" for repo in result])
            html = f.read().format(repos=repo_html, user_name=request.session["user"]["login"])
            return HTMLResponse(html)
    
    return RedirectResponse(f"{BASE_URL}/notfound")


async def handle_authorize_redirect(request: Request) -> Optional[Response]:
    """
    Checks to see if the request is an incoming redirect from the GitHub authorize URL.

    If it is, get an access token and store it in the session for further requests. If not,
    return None.
    """
    query_params = request.query_params

    code = query_params.get("code", None)
    state = query_params.get("state", None)
    if code and state:
        if state != request.session.get("state", None):
            return RedirectResponse(f"{BASE_URL}?error=invalid_state")
        result = await make_api_request(TOKEN_URL, request, "post", params={
            "grant_type": "authorization_code",
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "redirect_uri": f"{BASE_URL}github/callback",
            "code": code
        })

        token = result.get("access_token", None)
        if not token:
            return RedirectResponse(f"{BASE_URL}?error=bad_token")
        request.session["access_token"] = token
        return RedirectResponse(f"{BASE_URL}github")
    else:
        return None


async def make_api_request(url: str, request: Request, method: str, headers: dict = {}, params: dict = {}) -> dict:
    """
    Helper function to make an API request to the GitHub API
    """
    headers.update({
        "Accept": "application/json",
        "User-Agent": BASE_URL
    })

    access_token = request.session.get("access_token")

    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    res = requests.request(method, url, headers=headers, params=params)
    return res.json()


async def github_homepage(request: Request):
    """
    Main GitHub homepage
    """
    query_params = request.query_params

    authorize_response = await handle_authorize_redirect(request)
    if authorize_response:
        return authorize_response

    if query_params.get("action"):
        response = await handle_action(request)
        return response
    else:
        if not request.session.get("access_token"):    
            with open("./github/logged_out.html", "r") as f:
                html = f.read()
            return HTMLResponse(html)
        else:
            with open("./github/logged_in.html", "r") as f:
                res = await make_api_request(f"{API_URL_BASE}user", request, "get")
                user_name = res["login"]
                html = f.read().format(user_name=user_name)
            return HTMLResponse(html)