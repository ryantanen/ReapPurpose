import uuid

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel


# SQL Models

class User(SQLModel, table=True):
    __tablename__ = 'user'
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    company: str
    email: str = Field(default=None, nullable=True)
    hashed_password: str
    email_verified: bool = Field(default=False)
    
    # Add these relationship definitions
    pantry_items: list["PantryItem"] = Relationship(back_populates="user")
    statistics: list["Statistics"] = Relationship(back_populates="user")

class PantryItem(SQLModel, table=True):
    __tablename__ = 'pantry_items'
    name: str
    expires_at: str
    lastest_scan_time: str
    quantity: int
    user_id: uuid.UUID = Field(foreign_key='user.id')
    user: User = Relationship(back_populates='pantry_items')
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

class Statistics(SQLModel, table=True):
    __tablename__ = 'statistics'
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key='user.id')
    user: User = Relationship(back_populates='statistics')
    tracked_items: int
    items_used: int
    total_items: int
    enviroment_impact_co2: float
    enviroment_impact_water: float

# API Models
class UserCreate(BaseModel):
    company: str
    email: str | None = None
    verified: bool | None = None
    password: str

class UserRead(BaseModel):
    id: uuid.UUID
    company: str
    email: str | None = None
    verified: bool | None = None


class PantryItemCreate(BaseModel):
    name: str
    expires_at: str
    lastest_scan_time: str
    quantity: int
    
class PantryItemRead(BaseModel):
    name: str
    expires_at: str
    lastest_scan_time: str
    quantity: int
    user_id: uuid.UUID

class PantryRead(SQLModel):
    data: list[PantryItem] = []
    total: int = 0

# Auth Models
class UserLogin(BaseModel):
    user: UserRead
    access_token: str
    token_type: str = 'bearer'