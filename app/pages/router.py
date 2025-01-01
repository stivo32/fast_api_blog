from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dao import BlogDAO
from app.api.schemas import BlogFullResponse, BlogNotFound
from app.api.dependencies import get_blog_info
from app.api.utils import convert_blog_model
from app.auth.dependencies import get_current_user_optional
import markdown2

from app.auth.models import User
from app.dao.session_maker import SessionDep

router = APIRouter(tags=['Frontend'])

templates = Jinja2Templates(directory='app/templates')


@router.get('/blogs/{blog_id}/')
async def get_blog_post(
        request: Request,
        blog_id: int,
        blog_info: BlogFullResponse | BlogNotFound = Depends(get_blog_info),
        user_data: User | None = Depends(get_current_user_optional)
):
    if isinstance(blog_info, BlogNotFound):
        return templates.TemplateResponse(
            "404.html", {"request": request, "blog_id": blog_id}
        )
    else:
        blog = blog_info.model_dump()
        blog['content'] = markdown2.markdown(blog['content'], extras=['fenced-code-blocks', 'tables'])
        return templates.TemplateResponse(
            "post.html",
            {"request": request, "article": blog, "current_user_id": user_data.id if user_data else None}
        )


@router.get('/blogs/')
async def get_blog_post(
        request: Request,
        author_id: int | None = None,
        tag: str | None = None,
        page: int = 1,
        page_size: int = 3,
        session: AsyncSession = SessionDep,
):
    blogs = await BlogDAO.get_blog_list(
        session=session,
        author_id=author_id,
        tag=tag,
        page=page,
        page_size=page_size
    )
    return templates.TemplateResponse(
        "posts.html",
        {
            "request": request,
            "article": blogs,
            "filters": {
                "author_id": author_id,
                "tag": tag,
            }
        }
    )