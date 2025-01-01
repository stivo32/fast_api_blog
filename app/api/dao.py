from loguru import logger
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.api.models import Tag, Blog, BlogTag
from app.api.schemas import BlogFullResponse, Author
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

    @classmethod
    async def delete_blog(cls, session: AsyncSession, blog_id: int, author_id: int) -> dict:
        query = select(cls.model).filter_by(id=blog_id)
        result = await session.execute(query)
        blog = result.scalar_one_or_none()

        if not blog:
            return {
                'message': f'Blog with ID "{blog_id}" is not found',
                'status': 'error',
            }

        if blog.author != author_id:
            return {
                'message': f'You don\'t have permissions to delete this blog',
                'status': 'error',
            }

        await session.delete(blog)
        await session.flush()

        return {
            'message': f"Blog with ID {blog_id} successfully deleted.",
            'status': 'success'
        }

    @classmethod
    async def change_blog_status(cls, session: AsyncSession, blog_id: int, new_status: str, author_id: int) -> dict:
        query = select(cls.model).filter_by(id=blog_id)
        result = await session.execute(query)
        blog = result.scalar_one_or_none()

        if not blog:
            return {
                'message': f'Blog with ID "{blog_id}" is not found',
                'status': 'error',
            }

        if blog.author != author_id:
            return {
                'message': f'You don\'t have permissions to change status of this blog',
                'status': 'error',
            }

        if blog.status == new_status:
            return {
                'message': f"Blog already has status '{new_status}'.",
                'status': 'info',
                'blog_id': blog_id,
                'current_status': new_status
            }

        blog.status = new_status
        await session.flush()

        return {
            'message': f"Status changed to '{new_status}'.",
            'status': 'success',
            'blog_id': blog_id,
            'new_status': new_status
        }

    @classmethod
    async def get_blog_list(
            cls,
            session: AsyncSession,
            author_id: int | None,
            tag: str | None,
            page: int = 1,
            page_size: int = 10
    ) -> dict:
        page_size = max(3, min(page_size, 100))
        page = max(1, page)

        base_query = select(cls.model).options(
            joinedload(cls.model.user),
            selectinload(cls.model.tags)
        ).filter_by(status='published')

        if author_id is not None:
            base_query = base_query.filter_by(author=author_id)

        if tag is not None:
            base_query = base_query.join(cls.model.tags).filter(cls.model.tags.any(Tag.name.ilike(f"%{tag.lower()}%")))

        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await session.scalar(count_query)

        if not total_result:
            return {
                "page": page,
                "total_page": 0,
                "total_result": 0,
                "blogs": []
            }

        total_page = (total_result + page_size - 1) // page_size

        offset = (page - 1) * page_size
        paginated_query = base_query.offset(offset).limit(page_size)

        result = await session.execute(paginated_query)
        blogs = result.scalars().all()

        unique_blogs = []
        seen_ids = set()
        for blog in blogs:
            if blog.id not in seen_ids:
                unique_blogs.append(BlogFullResponse(
                    title=blog.title,
                    content=blog.content,
                    short_description=blog.short_description,
                    status=blog.status,
                    author=Author.model_validate(
                        blog.user
                    ),
                    tags=[tag.name for tag in blog.tags]
                ))
                seen_ids.add(blog.id)

        filters = []
        if author_id is not None:
            filters.append(f"author_id={author_id}")
        if tag:
            filters.append(f"tag={tag}")
        filter_str = " & ".join(filters) if filters else "no filters"

        logger.info(f"Page {page} fetched with {len(blogs)} blogs, filters: {filter_str}")

        return {
            "page": page,
            "total_page": total_page,
            "total_result": total_result,
            "blogs": unique_blogs
        }


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
