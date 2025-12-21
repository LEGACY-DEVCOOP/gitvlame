from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from app.config import settings
from app.database import _ensure_prisma_client
from app.utils.exceptions import UnauthorizedException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_db():
    prisma = _ensure_prisma_client()
    if not prisma.is_connected():
        await prisma.connect()
    return prisma

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise UnauthorizedException()
    except jwt.PyJWTError:
        raise UnauthorizedException()
    
    prisma = await get_db()
    user = await prisma.user.find_unique(where={"id": user_id})
    if user is None:
        raise UnauthorizedException()
    return user
