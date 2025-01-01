from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dao import BlogDAO, TagDAO, BlogTagDAO
from app.api.schemas import BlogCreateSchemaBase, BlogCreateSchemaAdd
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.dao.session_maker import TransactionSessionDep

router = APIRouter(prefix='/api', tags=['API'])


@router.post('/blog/', summary='Add new blog post')
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
            await BlogTagDAO.add_blog_tags(session=session, blog_tag_pairs=[
                {'blog_id': blog_id, 'tag_id': tag_id} for tag_id in tags_ids
            ]
            )
        return {'status': 'success', 'message': f'Blog with id {blog_id} successfully added.'}
    except IntegrityError as e:
        if 'UNIQUE constraint failed' in str(e.orig):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUESTS, detail='Blog with this name already exists')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Error while blog adding')
