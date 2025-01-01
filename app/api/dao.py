from loguru import logger
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.api.models import Tag, Blog, BlogTag
from app.dao.base import BaseDAO


class TagDAO(BaseDAO):
    model = Tag

    @classmethod
    async def add_tags(cls, session: AsyncSession, tag_names: list[str]) -> list[int]:

        tag_ids = []
        for tag_name in tag_names:
            tag_name = tag_name.lower()
            stmt = select(cls.model).filter(cls.model.name == tag_name)
            result = await session.execute(stmt)

            tag = result.scalars().first()

            if tag:
                tag_ids.append(tag.id)
            else:
                new_tag = cls.model(name=tag_name)
                session.add(new_tag)
                try:
                    await session.flush()
                    logger.info(f"Tag '{tag_name}' is added")
                    tag_ids.append(new_tag.id)
                except SQLAlchemyError as e:
                    await session.rollback()
                    logger.error(f"Error while creating tag '{tag_name}': {e}")
                    raise e
        return tag_ids


class BlogDAO(BaseDAO):
    model = Blog

    @classmethod
    async def get_full_blog_info(cls, session: AsyncSession, blog_id: int):
        query = (
            select(cls.model)
            .options(
                joinedload(Blog.user),
                selectinload(Blog.tags),
            )
            .filter_by(id=blog_id)
        )

        result = await session.execute(query)
        return result.scalar_one_or_none()


class BlogTagDAO(BaseDAO):
    model = BlogTag

    @classmethod
    async def add_blog_tags(cls, session: AsyncSession, blog_tag_pairs: list[dict]) -> None:
        blog_tag_instances = []
        for pair in blog_tag_pairs:
            blog_id = pair.get('blog_id')
            tag_id = pair.get('tag_id')
            if blog_id and tag_id:
                blog_tag = cls.model(blog_id=blog_id, tag_id=tag_id)
                blog_tag_instances.append(blog_tag)
            else:
                logger.warning(f'Bad pair: {pair}')

        if blog_tag_instances:
            session.add_all(blog_tag_instances)
            try:
                await session.flush()
                logger.info(f'tag-blog pairs added: {len(blog_tag_instances)}')
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f'Error while adding tag-blog pair: {e}')
                raise e
        else:
            logger.warning('No data for adding to blogtags table')
