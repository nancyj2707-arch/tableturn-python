"""Domain refusals and the error types. No FastAPI or Starlette import: services raise these, and
`handlers.py` turns them into application/problem+json.

The class attributes below are the single source of truth for status, type and title. Routes never build error
responses; services raise, the handler maps.
"""


class DomainError(Exception):
    status: int = 400
    type: str = "/errors/domain"
    title: str = "Refused"

    def __init__(self, detail: str, **extra):
        super().__init__(detail)
        self.detail = detail
        self.extra = extra


class NoSuchBranch(DomainError):
    status, type, title = 404, "/errors/no-such-branch", "No such branch"


class NoSuchTable(DomainError):
    status, type, title = 404, "/errors/no-such-table", "No such table"


class NoSuchParty(DomainError):
    status, type, title = 404, "/errors/no-such-party", "No such party"


class NoSuchSeating(DomainError):
    status, type, title = 404, "/errors/no-such-seating", "No such seating"


class PartyTooBig(DomainError):
    status, type, title = 400, "/errors/party-too-big", "No table here could seat that many"


class TableTooSmall(DomainError):
    status, type, title = 409, "/errors/table-too-small", "The table is too small for the party"


class AlreadySeated(DomainError):
    status, type, title = 409, "/errors/already-seated", "The party is already at a table"


class TableNotCleared(DomainError):
    status, type, title = 409, "/errors/table-not-cleared", "The table has not been cleared"


class AlreadyLeft(DomainError):
    status, type, title = 409, "/errors/already-left", "The party has already left"


class NotLeftYet(DomainError):
    status, type, title = 409, "/errors/not-left-yet", "The party has not left yet"


class AlreadyCleared(DomainError):
    status, type, title = 409, "/errors/already-cleared", "The table has already been cleared"


# (status, type, title) of the errors the framework raises rather than a service: 422 for a body that fails validation
# and 400 for a query parameter that does ("filter values outside the enum are 400"), 404/405 for a path or
# a method the app does not serve (every error is problem+json).
VALIDATION_BODY = (422, "/errors/validation", "The request body is not valid")
VALIDATION_QUERY = (400, "/errors/validation", "Invalid filter value")
NOT_FOUND = (404, "/errors/not-found", "No such resource")
METHOD_NOT_ALLOWED = (405, "/errors/method-not-allowed", "Method not allowed")
HTTP = "/errors/http"