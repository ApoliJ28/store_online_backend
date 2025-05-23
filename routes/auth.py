from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel, Field
from users.models import Users
from passlib.context import CryptContext
from typing import Annotated
from sqlalchemy.orm import Session
from database import SessionLocal
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import timedelta, datetime, timezone
from dotenv import dotenv_values

config = dotenv_values(".env")

router = APIRouter(prefix="/api/auth", tags=["auth"])


class Token(BaseModel):
    access_token: str
    token_type: str

    class Config:
        json_schema_extra = {
            "example": {"access_token": "token obtenido", "token_type": "tipo de token"}
        }


class CreateUserRequest(BaseModel):
    username: str
    email: str
    firts_name: str
    last_name: str
    password: str = Field(min_length=6)
    role: str

    class Config:
        json_schema_extra = {
            "example": {
                "username": "usuario",
                "email": "email@example.com",
                "firts_name": "Nombre",
                "last_name": "Apellido",
                "password": "password",
                "role": "role",
            }
        }


bycrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl=f"{router.prefix}/token")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
db_dependency = Annotated[Session, Depends(get_db)]


def authenticate_user(username: str, password: str, db):
    user:Users = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not bycrypt_context.verify(password, user.hashed_password):
        return False
    return user


def create_access_token(
    username: str, user_id: int, role: str, expires_delta: timedelta
):
    encode = {"sub": username, "id": user_id, "role": role}
    datetime.date
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp": expires})

    return jwt.encode(encode, config["SECRET_KEY"], algorithm=config["ALGORITHM"])


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(
            token, config["SECRET_KEY"], algorithms=config["ALGORITHM"]
        )
        username: str = payload.get("sub")
        user_id: str = payload.get("id")
        user_role: str = payload.get("role")
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "message": "User not authorized.",
                    "data": [],
                    "succcess": False,
                    "error": "Could not validate user.",
                },
            )

        return {"username": username, "user_id": user_id, "user_role": user_role}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "User not authorized.",
                "data": [],
                "succcess": False,
                "error": "Could not validate user.",
            },
        )


user_dependency = Annotated[dict, Depends(get_current_user)]


@router.post("/", status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_user(
    db: db_dependency, user: user_dependency, create_user_request: CreateUserRequest
):

    if user is None or user.get("user_role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "user does not have permissions to create users.",
                "data": [],
                "succcess": False,
                "error": "Authentication Failed",
            },
        )

    user_request = (
        db.query(Users)
        .filter(
            Users.username == create_user_request.username
            or Users.email == create_user_request.email
        )
        .first()
    )
    if user_request:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail={
                "message": "User not created.",
                "data": [],
                "succcess": False,
                "error": f"error email or username already exist",
            },
        )

    create_user_model = Users(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.firts_name,
        last_name=create_user_request.last_name,
        role=create_user_request.role,
        hashed_password=bycrypt_context.hash(create_user_request.password),
        is_active=True,
    )
    try:
        db.add(create_user_model)
        db.commit()
        return {
            "detail": {
                "message": "User created.",
                "data": create_user_request,
                "succcess": True,
                "error": "",
            }
        }
    except:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail={
                "message": "User not created.",
                "data": [],
                "succcess": False,
                "error": f"error creating user.",
            },
        )


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "User not authorized.",
                "data": [],
                "succcess": False,
                "error": "Failed Authentication.",
            },
        )

    token = create_access_token(
        user.username, user.id, user.role, timedelta(minutes=60)
    )
    return {"access_token": token, "token_type": "bearer"}
