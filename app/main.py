from fastapi import FastAPI
from .routers import users,urls
from . import models
from .database import engine

models.Base.metadata.create_all(bind = engine)
""" REMEMBER: TO implement timely deletion on expired URLS"""

app = FastAPI()
app.include_router(users.router)
app.include_router(urls.router)

@app.get("/")
def root():
    return {"message": "Hello World"}

