from pydantic import ConfigDict, BaseModel

from app.auth.schemas import UserBase


class BaseModelConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BlogCreateSchemaBase(BaseModelConfig):
    title: str
    content: str
    short_description: str
    tags: list[str] = []


class BlogCreateSchemaAdd(BlogCreateSchemaBase):
    author: int


class BlogNotFound(BaseModelConfig):
    message: str
    status: str = 'Error'


class BlogFullResponse(BaseModelConfig):
    title: str
    content: str
    short_description: str
    status: str
    author: UserBase
    tags: list[str]


class Author(UserBase):
    ...
