from typing import TypedDict


class TypeLoginData(TypedDict):
    email: str
    password: str


_data = {
    "email": ...,
    "password": ...,
}


def login(data: TypeLoginData):
    email = data["abc"]