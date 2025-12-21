from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.database import connect_db, disconnect_db
from app.routers import auth, github, judgments, blame
from app.utils.exceptions import (
    UnauthorizedException,
    ForbiddenException,
    NotFoundException,
    GitHubAPIException,
    ClaudeAPIException,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await disconnect_db()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
@app.exception_handler(UnauthorizedException)
async def unauthorized_exception_handler(request: Request, exc: UnauthorizedException):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"message": "Unauthorized"},
    )

@app.exception_handler(ForbiddenException)
async def forbidden_exception_handler(request: Request, exc: ForbiddenException):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"message": "Forbidden"},
    )

@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request: Request, exc: NotFoundException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"message": "Not Found"},
    )

@app.exception_handler(GitHubAPIException)
async def github_api_exception_handler(request: Request, exc: GitHubAPIException):
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"message": "GitHub API Error", "detail": str(exc)},
    )

@app.exception_handler(ClaudeAPIException)
async def claude_api_exception_handler(request: Request, exc: ClaudeAPIException):
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"message": "Claude API Error", "detail": str(exc)},
    )

# Routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(github.router, prefix="/github", tags=["github"])
app.include_router(judgments.router, prefix="/judgments", tags=["judgments"])
app.include_router(blame.router, prefix="/judgments", tags=["blame"])
# Let's check the prompt requirements for routers. 
# Blame router endpoints start with /judgments/{judgment_id}/blame. 
# I will include it without prefix here and define full paths in the router, or use a prefix. 
# Usually it's cleaner to use prefix. But let's wait until I create the router files to uncomment this.
# For now I will comment out the routers that don't exist yet to avoid import errors if I were to run it.
# But since I am creating files sequentially, I will leave them imported but I need to make sure I create them next.
# Actually, to prevent runtime errors if the user tries to run it immediately, I should probably create empty router files or comment them out.
# However, the plan is to create them all. I will assume I will create them shortly.
# Wait, `app.routers` package needs to exist. I saw `app/routers` directory earlier.
# I will comment out the imports and include_router for now, or just create empty files.
# The prompt asks for `app/main.py` to register them. I will write the code assuming they exist or will exist.
# I'll stick to the prompt's request.
