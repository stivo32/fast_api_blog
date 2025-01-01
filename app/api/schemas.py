from pydantic import ConfigDict, BaseModel


class BaseModelConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BlogCreateSchemaBase(BaseModelConfig):
    title: str
    content: str
    short_description: str
    tags: list[str] = []


class BlogCreateSchemaAdd(BlogCreateSchemaBase):
    author: int
