import os

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from auth import create_admin_token, verify_admin_token
from config import settings

router = APIRouter()

_tmpl_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=_tmpl_dir)


def _is_admin(request: Request) -> bool:
    token = request.cookies.get(settings.cookie_name)
    return bool(token and verify_admin_token(token))


def _redirect_login() -> RedirectResponse:
    return RedirectResponse(url="/ui/login", status_code=302)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if _is_admin(request):
        return RedirectResponse(url="/ui/", status_code=302)
    return templates.TemplateResponse(request, "login.html")


@router.post("/login")
async def login(request: Request, password: str = Form(...)):
    if password != settings.admin_password:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Invalid password"},
            status_code=401,
        )
    token = create_admin_token()
    resp = RedirectResponse(url="/ui/", status_code=302)
    resp.set_cookie(
        settings.cookie_name,
        token,
        httponly=True,
        samesite="lax",
        max_age=settings.jwt_expire_hours * 3600,
    )
    return resp


@router.get("/logout")
async def logout():
    resp = RedirectResponse(url="/ui/login", status_code=302)
    resp.delete_cookie(settings.cookie_name)
    return resp


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    if not _is_admin(request):
        return _redirect_login()
    return templates.TemplateResponse(request, "dashboard.html", {"active": "dashboard"})


@router.get("/keys", response_class=HTMLResponse)
async def keys_page(request: Request):
    if not _is_admin(request):
        return _redirect_login()
    return templates.TemplateResponse(request, "keys.html", {"active": "keys"})


@router.get("/usage", response_class=HTMLResponse)
async def usage_page(request: Request):
    if not _is_admin(request):
        return _redirect_login()
    return templates.TemplateResponse(request, "usage.html", {"active": "usage"})
