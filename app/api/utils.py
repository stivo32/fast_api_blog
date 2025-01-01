from app.api.models import Blog
from app.api.schemas import BlogFullResponse, Author


def convert_blog_model(blog: Blog) -> BlogFullResponse:
    return BlogFullResponse(
        id=blog.id,
        title=blog.title,
        content=blog.content,
        short_description=blog.short_description,
        status=blog.status,
        author=Author(
            author_id=blog.user.id,
            author_name=f'{blog.user.first_name} {blog.user.last_name}'
        ),
        tags=[tag.name for tag in blog.tags],
        created_at=blog.created_at,
    )