from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from src.users.models import Users
from database import SessionLocal
from sqlalchemy.orm import Session
from .auth import get_current_user
from passlib.context import CryptContext
from src.users.schemas import UserVerification

router = APIRouter(
    prefix='/api//users',
    tags=['users']
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]
bycrypt_context = CryptContext(schemes= ['bcrypt'], deprecated= 'auto')


@router.get('/', status_code= status.HTTP_200_OK)
async def get_user(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail= {
            'message':"Not authorized.",
            'data':[],
            'succcess':False,
            'error':'Authentication Failed'
            })
    return db.query(Users).filter(Users.id == user.get('user_id')).first()

@router.put('/password', status_code= status.HTTP_204_NO_CONTENT)
async def change_password(user: user_dependency, db: db_dependency, user_verification: UserVerification):
    if user is None:
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail={
                            'message':"Not authorized.",
                            'data':[],
                            'succcess':False,
                            'error':'Authentication Failed'
                            })
    user_model = db.query(Users).filter(Users.id == user.get('user_id')).first()
    
    if not bycrypt_context.verify(user_verification.password, user_model.hashed_password):
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail={
                                'message':"Error on password change",
                                'data':[],
                                'succcess':False,
                                'error':'Does not match the current password'
                                })
    user_model.hashed_password = bycrypt_context.hash(user_verification.new_password)
    db.add(user_model)
    db.commit()
