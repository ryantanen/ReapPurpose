from typing import Optional
import requests
from pydantic import BaseModel
from sqlmodel import Session, select
from models import KnownProduct, KnownProductCreate
from datetime import datetime

class ProductInfo(BaseModel):
    name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    error: Optional[str] = None
    is_known_product: bool = False

def get_known_product(barcode: str, db: Session) -> Optional[ProductInfo]:
    """
    Check if the product exists in our known products database.
    """
    statement = select(KnownProduct).where(KnownProduct.barcode == barcode)
    known_product = db.exec(statement).first()
    
    if known_product:
        return ProductInfo(
            name=known_product.name,
            brand=known_product.brand,
            category=known_product.category,
            is_known_product=True
        )
    return None

def save_known_product(product: KnownProductCreate, user_id: str, db: Session) -> KnownProduct:
    """
    Save a new product to the known products database.
    """
    known_product = KnownProduct(
        **product.dict(),
        created_by=user_id,
        updated_at=datetime.now().isoformat()
    )
    db.add(known_product)
    db.commit()
    db.refresh(known_product)
    return known_product

def process_barcode(barcode: str, db: Session) -> ProductInfo:
    """
    Process a barcode and return product information.
    First checks known products, then falls back to Open Food Facts API.
    
    Args:
        barcode (str): The barcode to process
        db (Session): Database session
        
    Returns:
        ProductInfo: Object containing product information or error message
    """
    # First check known products
    known_product = get_known_product(barcode, db)
    if known_product:
        return known_product
        
    try:
        # Open Food Facts API endpoint
        url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
        response = requests.get(url)
        data = response.json()
        
        if data.get("status") == 1 and data.get("product"):
            product = data["product"]
            return ProductInfo(
                name=product.get("product_name", "Unknown Product"),
                brand=product.get("brands"),
                category=product.get("categories")
            )
        else:
            return ProductInfo(
                name="Unknown Product",
                error="Product not found in database"
            )
            
    except Exception as e:
        return ProductInfo(
            name="Unknown Product",
            error=f"Error processing barcode: {str(e)}"
        )
