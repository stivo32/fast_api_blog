from sqlalchemy import ForeignKey, Text, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.dao.database import Base, str_uniq


class Blog(Base):
    title: Mapped[str_uniq]
    author: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text)
    short_description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(default="published", server_default="published")
    user: Mapped["User"] = relationship("User", back_populates="blogs")
    tags: Mapped[list["Tag"]] = relationship(
        secondary="blogtags",
        back_populates="blogs",
    )


class Tag(Base):
    name: Mapped[str] = mapped_column(String(50), unique=True)
    blogs: Mapped[list["Blog"]] = relationship(
        secondary="blogtags",
        back_populates="tags",
    )


class BlogTag(Base):
    blog_id: Mapped[int] = mapped_column(ForeignKey("blogs.id", ondelete="CASCADE"), nullable=False)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        UniqueConstraint("blog_id", 'tag_id', name='uq_blog_tag'),
    )

