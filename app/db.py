from sqlmodel import create_engine, Session, SQLModel
from env import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=True)

def get_db():
    with Session(engine) as session:
        yield session

# Create tables
def create_tables():
    SQLModel.metadata.create_all(engine)