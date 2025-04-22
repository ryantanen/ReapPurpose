from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from auth.auth import get_current_user, login, create_user
from sqlmodel import Session, select
from models import User, PantryItem, PantryRead, PantryItemCreate, PantryItemRead, UserCreate, UserLogin, UserRead, KnownProduct, KnownProductCreate, KnownProductRead
from db import get_db
from scan import process_barcode, ProductInfo, save_known_product, get_known_product

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
    print(form_data.username, form_data.password)
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
    # Only check known_products if there's a barcode
    if pantry_item.barcode:
        known_product = get_known_product(pantry_item.barcode, db)
        if not known_product:
            # If not found, create a new known product
            try:
                new_product = KnownProductCreate(
                    barcode=pantry_item.barcode,
                    name=pantry_item.name,
                    brand=None,  # These can be added later if needed
                    category=None
                )
                save_known_product(new_product, user.id, db)
            except Exception as e:
                print(f"Error saving known product: {e}")
                # Continue with pantry item creation even if known product save fails

    # Create the pantry item
    new_pantry_item = PantryItem(
        barcode=pantry_item.barcode,
        name=pantry_item.name, 
        expires_at=pantry_item.expires_at, 
        lastest_scan_time=pantry_item.lastest_scan_time,
        quantity=pantry_item.quantity,
        user_id=user.id
    )
    
    try:
        db.add(new_pantry_item)
        db.commit()
        db.refresh(new_pantry_item)
        return new_pantry_item
    except Exception as e:
        db.rollback()
        print(e)
        raise HTTPException(status_code=400, detail="Error creating pantry item")

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

@app.delete("/pantry/item/{item_id}", response_model=PantryItemRead)
def delete_pantry_item(item_id: str, user: Annotated[User, Depends(get_current_user)], db: Session=Depends(get_db)):
    statement = select(PantryItem).where(PantryItem.user_id == user.id, PantryItem.id == item_id)
    pantry_item = db.exec(statement=statement).first()
    if not pantry_item:
         raise HTTPException(status_code=400, detail="Could not find item") 
    
    # Store the item data before deletion for the response
    item_data = PantryItemRead(
        id=pantry_item.id,
        barcode=pantry_item.barcode,
        name=pantry_item.name,
        expires_at=pantry_item.expires_at,
        lastest_scan_time=pantry_item.lastest_scan_time,
        quantity=pantry_item.quantity
    )
    
    db.delete(pantry_item)
    db.commit()
    return item_data

@app.get("/scan/{barcode}", response_model=ProductInfo)
def scan_barcode(barcode: str, db: Session = Depends(get_db)):
    """
    Process a scanned barcode and return product information.
    First checks known products, then falls back to Open Food Facts API.
    """
    return process_barcode(barcode, db)

@app.post("/known-product", response_model=KnownProductRead)
def create_known_product(
    product: KnownProductCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """
    Save a new product to the known products database.
    """
    try:
        return save_known_product(product, user.id, db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error saving product: {str(e)}")

@app.get("/known-product/{barcode}", response_model=KnownProductRead)
def get_known_product_info(
    barcode: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """
    Get information about a known product.
    """
    statement = select(KnownProduct).where(KnownProduct.barcode == barcode)
    product = db.exec(statement).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product