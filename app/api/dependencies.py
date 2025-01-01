from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dao import BlogDAO
from app.api.models import Blog
from app.api.schemas import BlogNotFound, BlogFullResponse, Author
from app.api.utils import convert_blog_model
from app.auth.dependencies import get_current_user_optional
from app.auth.models import User
from app.dao.session_maker import SessionDep


async def get_blog_info(
        blog_id: int,
        session: AsyncSession = SessionDep,
        user_data: User | None = Depends(get_current_user_optional)
) -> BlogFullResponse | BlogNotFound:
    author_id = user_data.id if user_data else None
    result = await BlogDAO.get_full_blog_info(session=session, blog_id=blog_id)
    if not result:
        return BlogNotFound(
            message=f'Blog with ID "{blog_id}" does not exist or you have no enough permissions',
        )
    if isinstance(result, Blog):
        if result.status == 'draft' and (author_id != result.author):
            return BlogNotFound(
                message='This blog is in draft status, only author has access to it',
            )
        return convert_blog_model(result)
