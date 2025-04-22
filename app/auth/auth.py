from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from env import AUTH_SECRET_KEY
from models import User, UserLogin, UserCreate, UserRead, Statistics
from typing import Annotated
from fastapi import Depends, HTTPException, status
from sqlmodel import Session, select
from fastapi.security import OAuth2PasswordBearer
from db import get_db

import jwt


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 60 * 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def compare_pwd(plain, hashed):
    return pwd_context.verify(plain, hashed)

def get_pwd_hash(pwd):
    return pwd_context.hash(pwd)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, AUTH_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try: 
        payload = jwt.decode(token, AUTH_SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = db.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise credentials_exception
    
    return user

def get_active_user(current_user: Annotated[User, Depends(get_current_user)]):
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not verified",
        )
    return current_user

def login(db: Session, email: str, password: str):
    user = db.exec(select(User).where(User.email == email)).first()
    if not user:
        return None
    if not compare_pwd(password, user.hashed_password):
        return None
    
    # Get user's statistics to get used_items count
    stats = db.exec(select(Statistics).where(Statistics.user_id == user.id)).first()
    used_items = stats.items_used if stats else 0
    
    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"user_id": str(user.id)}, 
        expires_delta=expires_delta
    )

    return UserLogin(
        access_token=access_token, 
        user=UserRead(
            id=user.id, 
            company=user.company, 
            email=user.email, 
            verified=user.email_verified,
            used_items=used_items
        ), 
        token_type="bearer"
    )

def create_user(user_data: UserCreate, db: Session):
    if db.exec(select(User).where(User.email == user_data.email)).first():
        return None
    hashed_password = get_pwd_hash(user_data.password)
    user = User(
        email=user_data.email, 
        hashed_password=hashed_password, 
        company=user_data.company,
        email_verified=user_data.verified if user_data.verified is not None else False
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user