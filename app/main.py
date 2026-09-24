from fastapi import FastAPI, Depends
from .routers import users,urls
from . import models
from .database import engine,get_db

from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone
from sqlalchemy.orm import Session

models.Base.metadata.create_all(bind = engine)


def cleanup_expired_urls(db:Session = Depends(get_db)):
    try:
        now = datetime.now(timezone.utc)
        url_query = db.query(models.URLS).where(models.URLS.expires_at < now)
        url_query.delete(synchronize_session=False)
        db.commit()

    except Exception as e:
        db.rollback()
        print(f"Error during cleanup: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize and start the scheduler
    scheduler = BackgroundScheduler()

    # Run the cleanup job every hour
    scheduler.add_job(cleanup_expired_urls, 'interval', hours=1)
    scheduler.start()

    yield  # App is running

    # Shutdown: Cleanly shut down the scheduler
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)
app.include_router(users.router)
app.include_router(urls.router)

@app.get("/")
def root():
    return {"message": "Hello World"}

