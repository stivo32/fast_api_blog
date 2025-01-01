from datetime import datetime, timezone

from fastapi import Request, HTTPException, status, Depends
from jose import jwt, JWTError
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dao import UsersDAO
from app.auth.models import User
from app.config import settings
from app.dao.session_maker import SessionDep
from app.exceptions import TokenExpiredException, NoJwtException, NoUserIdException, ForbiddenException, TokenNoFound


def get_token(request: Request):
    token = request.cookies.get('users_access_token')
    if not token:
        raise TokenNoFound
    return token


def get_token_optional(request: Request):
    return request.cookies.get('users_access_token')


async def get_current_user(token: str = Depends(get_token), session: AsyncSession = SessionDep):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=settings.ALGORITHM)
    except JWTError:
        raise NoJwtException

    user_id: str = payload.get('sub')
    if not user_id:
        raise NoUserIdException

    user = await UsersDAO.find_one_or_none_by_id(data_id=int(user_id), session=session)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found')
    return user


async def get_current_user_optional(
        token: str | None = Depends(get_token_optional),
        session: AsyncSession = SessionDep,
) -> User | None:
    if token is None:
        return None

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=settings.ALGORITHM)
    except JWTError:
        return None

    user_id = payload.get('sub')

    if not user_id:
        return None

    user = await UsersDAO.find_one_or_none_by_id(data_id=int(user_id), session=session)
    return user


async def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role.id in [3, 4]:
        return current_user
    raise ForbiddenException
