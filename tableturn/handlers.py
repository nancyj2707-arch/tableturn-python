"""The one place errors become HTTP: every domain refusal and every validation failure is application/problem+json
built by `problem`."""
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .errors import (
    HTTP,
    METHOD_NOT_ALLOWED,
    NOT_FOUND,
    VALIDATION_BODY,
    VALIDATION_QUERY,
    DomainError,
)

PROBLEM = "application/problem+json"


def problem(status: int, type_: str, title: str, detail: str, headers: dict | None = None, **extra) -> JSONResponse:
    body = {"type": type_, "title": title, "status": status, "detail": detail, **extra}
    return JSONResponse(status_code=status, content=body, media_type=PROBLEM, headers=headers)


def install_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _domain(_request: Request, exc: DomainError):
        return problem(exc.status, exc.type, exc.title, exc.detail, **exc.extra)

    @app.exception_handler(RequestValidationError)
    async def _validation(_request: Request, exc: RequestValidationError):
        raw = exc.errors()
        errors = [{"field": ".".join(str(p) for p in e["loc"][1:]) or str(e["loc"][0]), "message": e["msg"]} for e in raw]
        in_body = any(e["loc"] and e["loc"][0] == "body" for e in raw)
        status, type_, title = VALIDATION_BODY if in_body else VALIDATION_QUERY
        return problem(status, type_, title, f"{len(errors)} field(s) failed validation", errors=errors)

    @app.exception_handler(StarletteHTTPException)
    async def _framework(request: Request, exc: StarletteHTTPException):
        if exc.status_code == NOT_FOUND[0]:
            status, type_, title = NOT_FOUND
            detail = f"There is nothing at {request.url.path}"
        elif exc.status_code == METHOD_NOT_ALLOWED[0]:
            status, type_, title = METHOD_NOT_ALLOWED
            detail = f"{request.method} is not allowed on {request.url.path}"
        else:
            status, type_, title = exc.status_code, HTTP, HTTPStatus(exc.status_code).phrase
            detail = str(exc.detail)
        return problem(status, type_, title, detail, headers=getattr(exc, "headers", None))   