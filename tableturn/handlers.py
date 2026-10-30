"""The one place errors become HTTP: every error body — domain refusals, validation, a path or method the app
does not serve, and the unexpected — is application/problem+json built by `problem`. Also the OpenAPI `responses`
entries the routers declare, so /docs shows how each endpoint can say no."""
import logging
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .errors import (
    HTTP,
    INTERNAL,
    METHOD_NOT_ALLOWED,
    NOT_FOUND,
    VALIDATION_BODY,
    VALIDATION_QUERY,
    DomainError,
)

log = logging.getLogger("tableturn.errors")

PROBLEM = "application/problem+json"


def problem(status: int, type_: str, title: str, detail: str, headers: dict | None = None, **extra) -> JSONResponse:
    body = {"type": type_, "title": title, "status": status, "detail": detail, **extra}
    return JSONResponse(status_code=status, content=body, media_type=PROBLEM, headers=headers)


def problem_entry(status: int, type_: str, title: str, detail: str, **extra) -> dict:
    """One OpenAPI `responses` entry with a problem+json example."""
    return {"description": title,
            "content": {PROBLEM: {"example": {"type": type_, "title": title, "status": status, "detail": detail, **extra}}}}


def example(cls: type[DomainError], detail: str, **extra) -> dict:
    """The `responses` entry for one domain refusal."""
    return problem_entry(cls.status, cls.type, cls.title, detail, **extra)


def responses(*entries: tuple[type[DomainError], str] | tuple[type[DomainError], str, dict]) -> dict:
    """Refusals that share a status are shown as one entry with every example, so none is hidden from /docs."""
    out: dict[int | str, dict] = {}
    for entry in entries:
        cls, detail = entry[0], entry[1]
        extra = entry[2] if len(entry) == 3 else {}
        item = example(cls, detail, **extra)
        if cls.status in out:
            existing = out[cls.status]
            examples = existing["content"][PROBLEM].setdefault("examples", {})
            if "example" in existing["content"][PROBLEM]:
                first = existing["content"][PROBLEM].pop("example")
                examples[first["type"]] = {"value": first}
            examples[cls.type] = {"value": item["content"][PROBLEM]["example"]}
            existing["description"] = existing["description"] + " · " + cls.title
        else:
            out[cls.status] = item
    return out




# A body that fails validation (POST /waitlist, POST /seatings).
VALIDATION_RESPONSE = {VALIDATION_BODY[0]: problem_entry(
    *VALIDATION_BODY, "1 field(s) failed validation",
    errors=[{"field": "covers", "message": "Input should be greater than or equal to 1"}])}

# A query parameter outside its enum (GET /branches/{branch}/tables?section=Roof).
FILTER_RESPONSE = {VALIDATION_QUERY[0]: problem_entry(
    *VALIDATION_QUERY, "1 field(s) failed validation",
    errors=[{"field": "section", "message": "Input should be 'Window', 'Garden' or 'Indoor'"}])}

# The one unexpected-error answer every operation can give.
INTERNAL_RESPONSE = {INTERNAL[0]: problem_entry(*INTERNAL, "The request could not be completed", request_id="3f9c2a7b1d04")}
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

    @app.exception_handler(Exception)
    async def _unexpected(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", "-")
        log.exception("unhandled error path=%s request_id=%s", request.url.path, request_id)
        status, type_, title = INTERNAL
        return problem(status, type_, title, "The request could not be completed", request_id=request_id)