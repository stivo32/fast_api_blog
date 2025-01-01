import re
from typing import Self
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator, computed_field
from app.auth.utils import get_password_hash


class EmailModel(BaseModel):
    email: EmailStr = Field(description="Email")
    model_config = ConfigDict(from_attributes=True)


class UserBase(EmailModel):
    phone_number: str = Field(description="Phone number, begins with '+'")
    first_name: str = Field(min_length=3, max_length=50, description="Name, from 3 to 50 symbols")
    last_name: str = Field(min_length=3, max_length=50, description="Last name, from 3 to 50 symbols")

    @field_validator("phone_number")
    def validate_phone_number(cls, value: str) -> str:
        if not re.match(r'^\+\d{5,15}$', value):
            raise ValueError('Phone number must begin with "+" and contain from 5 to 15 numbers')
        return value


class SUserRegister(UserBase):
    password: str = Field(min_length=5, max_length=50, description="Password, from 5 to 50 symbols")
    confirm_password: str = Field(min_length=5, max_length=50, description="Repeat password")

    @model_validator(mode="after")
    def check_password(self) -> Self:
        if self.password != self.confirm_password:
            raise ValueError("Passwords are not the same")
        self.password = get_password_hash(self.password)
        return self


class SUserAddDB(UserBase):
    password: str = Field(min_length=5, description="Password in hash format")


class SUserAuth(EmailModel):
    password: str = Field(min_length=5, max_length=50, description="Password, from 5 to 50 symbols")


class RoleModel(BaseModel):
    id: int = Field(description="Role id")
    name: str = Field(description="Role name")
    model_config = ConfigDict(from_attributes=True)


class SUserInfo(UserBase):
    id: int = Field(description="User id")
    role: RoleModel = Field(exclude=True)

    @computed_field
    def role_name(self) -> str:
        return self.role.name

    @computed_field
    def role_id(self) -> int:
        return self.role.id
