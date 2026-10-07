from app.database import engine
from app.models import Base

print("Connected database:", engine.url.database)

print("Tables before creation:")
print(Base.metadata.tables.keys())

Base.metadata.create_all(engine)

print("Tables created successfully.")

print("Tables known to SQLAlchemy:")
print(Base.metadata.tables.keys())