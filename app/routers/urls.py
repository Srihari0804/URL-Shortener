from datetime import datetime
from fastapi.responses import RedirectResponse
from fastapi import APIRouter,status, Depends, Security, HTTPException, Request
from .. import schemas, utils, models
from ..database import get_db
from sqlalchemy.orm import Session
from fastapi.security import APIKeyHeader
from typing import List

router = APIRouter(
    tags=["Urls"],
    prefix="/urls"
)
my_key_grabber = APIKeyHeader(name="API-Key")

@router.post("/shorten",status_code=status.HTTP_201_CREATED)
def create_shorturl(url_info:schemas.CreateShortURL, api_key:str = Security(my_key_grabber), db:Session = Depends(get_db)):
    user = utils.get_curr_user(api_key,db)
    while True:
        short_code = utils.generate_short_code()
        url = db.query(models.URLS).filter(models.URLS.short_code == short_code).first()
        if not url:
            break

    new_url = models.URLS(short_code = short_code, original_url = str(url_info.original_url),
                              user_id = user.id, expires_at = url_info.expires_at)

    db.add(new_url)
    db.commit()
    db.refresh(new_url)

    return {"original_url": new_url.original_url, "short_code": new_url.short_code, "expires_at":new_url.expires_at,
            "user_id":new_url.user_id}

@router.get("/me",response_model= List[schemas.URLSReturn])
def get_all_urls(api_key:str = Security(my_key_grabber),db:Session = Depends(get_db)):
    user = utils.get_curr_user(api_key, db)
    urls_by_user = db.query(models.URLS).filter(models.URLS.user_id == user.id).all()

    return urls_by_user

@router.get("/{id}/stats")
def get_stats(id:int, api_key:str = Security(my_key_grabber), db:Session = Depends(get_db)):
    user = utils.get_curr_user(api_key, db)
    url_row = db.query(models.URLS).filter(models.URLS.id == id).first()
    if not url_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Requested URL ID not present")

    if url_row.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail= "Unauthorized to this URL")

    stats = db.query(models.Clicks).filter(models.Clicks.url_id == id).all()

    return stats

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_url(id:int,api_key:str = Security(my_key_grabber),db:Session = Depends(get_db)):
    user = utils.get_curr_user(api_key, db)
    url_query = db.query(models.URLS).filter(models.URLS.id == id)

    url = url_query.first()
    if not url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="URL with this id Not present")

    if url.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Not Authorized")

    url_query.delete(synchronize_session = False)
    db.commit()

    return



@router.get("/{short_code}",status_code=status.HTTP_307_TEMPORARY_REDIRECT)
def redirect(short_code: str, request: Request, db:Session = Depends(get_db)):
    db_row = db.query(models.URLS).filter(models.URLS.short_code == short_code).first()

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    if not db_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Invalid short code")

    if db_row.expires_at and db_row.expires_at < datetime.now():
        raise HTTPException(status_code=status.HTTP_410_GONE,
                            detail="This short link has expired"
                            )
    new_click = models.Clicks(url_id = db_row.id,
                            ip_address = client_ip,
                            user_agent = user_agent)
    db.add(new_click)
    db.commit()

    return RedirectResponse(url=db_row.original_url,status_code=307)



