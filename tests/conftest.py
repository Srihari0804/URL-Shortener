import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.database import Base,get_db
from app.main import app

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:root@localhost/url_shortner_testing_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def session():
    Base.metadata.drop_all(bind=engine)   # wipe tables
    Base.metadata.create_all(bind=engine)  # create fresh tables
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(session):
    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)


@pytest.fixture
def auth_header(client: TestClient):
    payload = {
        "email": "url_tester@example.com",
        "password": "testpassword123"
    }
    response = client.post("/users/signup", json=payload)

    api_key = response.json()["api_key"]

    return {"API-Key": api_key}