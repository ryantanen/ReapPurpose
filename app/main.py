from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from auth.auth import get_current_user, login, create_user
from sqlmodel import Session, select
from models import User, PantryItem, PantryRead, PantryItemCreate, PantryItemRead, UserCreate, UserLogin, UserRead
from db import get_db, create_tables

create_tables()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "OK"}

@app.post("/login", response_model=UserLogin)
def get_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    result: UserLogin = login(db, email=form_data.username, password=form_data.password)
    if not result:
        raise HTTPException(status_code=401, detail="Credentials are not valid")
    return result

@app.get("/user/me", response_model=UserRead)
def get_user_info(current_user: Annotated[User, Depends(get_current_user)]):
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return UserRead(id=current_user.id, company=current_user.company, email=current_user.email, verified=current_user.email_verified)

@app.post("/user", response_model=UserRead)
def create_user_password(user: UserCreate, db: Session = Depends(get_db)):
    user: User = create_user(user, db)
    if not user:
        raise HTTPException(status_code=400, detail="User already exists")
    return UserRead(id=user.id, company=user.company, email=user.email, verified=user.email_verified)


@app.post("/pantry/item", response_model=PantryItemCreate)
def create_pantry_item(pantry_item: PantryItemCreate, user: Annotated[User, Depends(get_current_user)], db: Session = Depends(get_db)):
    pantry_item = PantryItem(
        name=pantry_item.name, 
        expires_at=pantry_item.expires_at, 
        lastest_scan_time=pantry_item.lastest_scan_time,
        quantity=pantry_item.quantity,
        user_id=user.id
    )
    db.add(pantry_item)
    try:
        db.commit()
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail="Error creating pantry item")
    if not pantry_item:
        raise HTTPException(status_code=400, detail="Pantry item already exists")
    db.refresh(pantry_item)
    return pantry_item

@app.get("/pantry/item/{item_id}", response_model=PantryItemRead)
def get_pantry_item(item_id: str, user: Annotated[User, Depends(get_current_user)], db: Session = Depends(get_db)):
    statement = select(PantryItem).where(PantryItem.id == item_id, User.id == user.id)
    pantry_item = db.exec(statement=statement).first()
    if not pantry_item:
        return {"error": "Pantry item not found"}
    return pantry_item


@app.get("/pantry/items", response_model=PantryRead)
def get_pantry_items(user: Annotated[User, Depends(get_current_user)], db: Session = Depends(get_db)):
    statement = select(PantryItem).where(PantryItem.user_id == user.id)
    pantry_items = db.exec(statement=statement).all()
    if not pantry_items:
        return PantryRead(data=[], total=0)
    return PantryRead(data=pantry_items, total=len(pantry_items))