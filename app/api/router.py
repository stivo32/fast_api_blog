from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends, Query
from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.api.dao import BlogDAO, TagDAO, BlogTagDAO
from app.api.dependencies import get_blog_info
from app.api.schemas import BlogCreateSchemaBase, BlogCreateSchemaAdd, BlogNotFound, BlogFullResponse
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.dao.session_maker import TransactionSessionDep, SessionDep

router = APIRouter(prefix='/api', tags=['API'])


@router.post('/blogs/', summary='Add new blog post')
async def add_blog(
        add_data: BlogCreateSchemaBase,
        user_data: User = Depends(get_current_user),
        session: AsyncSession = TransactionSessionDep,
):
    blog_dict = add_data.model_dump()
    blog_dict['author'] = user_data.id
    tags = blog_dict.pop('tags', [])

    try:
        blog = await BlogDAO.add(session=session, values=BlogCreateSchemaAdd.model_validate(blog_dict))
        blog_id = blog.id

        if tags:
            tags_ids = await TagDAO.add_tags(session=session, tag_names=tags)
            await BlogTagDAO.add_blog_tags(
                session=session,
                blog_tag_pairs=[
                    {'blog_id': blog_id, 'tag_id': tag_id} for tag_id in tags_ids
                ]
            )
        return {'status': 'success', 'message': f'Blog with id {blog_id} successfully added.'}
    except IntegrityError as e:
        if 'UNIQUE constraint failed' in str(e.orig):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUESTS, detail='Blog with this name already exists')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Error while blog adding')


@router.get('/blogs/{blog_id}', summary='Get blog info')
async def get_blog_endpoint(
        blog_id: int,
        blog_info: BlogFullResponse | BlogNotFound = Depends(get_blog_info),
) -> BlogFullResponse | BlogNotFound:
    return blog_info


@router.delete('/blogs/{blog_id}', summary="Delete blog")
async def delete_blog(
        blog_id: int,
        session: AsyncSession = TransactionSessionDep,
        current_user: User = Depends(get_current_user)
):
    result = await BlogDAO.delete_blog(session, blog_id, current_user.id)
    if result['status'] == 'error':
        raise HTTPException(status_code=400, detail=result['message'])
    return result


@router.patch('/blogs/{blog_id}', summary="Change blog status")
async def change_blog_status(
        blog_id: int,
        new_status: str,
        session: AsyncSession = TransactionSessionDep,
        current_user: User = Depends(get_current_user)
):
    result = await BlogDAO.change_blog_status(session, blog_id, new_status, current_user.id)
    if result['status'] == 'error':
        raise HTTPException(status_code=400, detail=result['message'])
    return result


@router.get('/blogs/', summary='get all blogs in Publish status')
async def get_blogs_info(
        author_id: Optional[int] = None,
        tag: Optional[str] = None,
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(10, ge=10, le=100, description="Records on page"),
        session: AsyncSession = SessionDep,
):
    try:
        result = await BlogDAO.get_blog_list(
            session=session,
            author_id=author_id,
            tag=tag,
            page=page,
            page_size=page_size,
        )
        return result if result['blogs'] else BlogNotFound(message='Blogs not found')
    except Exception as e:
        logger.error(f'Error while blogs fetching: {e}')
        return JSONResponse(status_code=500, content={'detail': 'Server error'})
