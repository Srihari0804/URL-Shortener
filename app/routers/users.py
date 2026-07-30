from fastapi import APIRouter,status, Depends, HTTPException, Security
from .. import schemas,models
from ..database import get_db
from .. import utils
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi.security import APIKeyHeader

router = APIRouter(
    tags=["users"],
    prefix="/users"
)

my_key_grabber = APIKeyHeader(name="API-Key")

@router.post("/signup",status_code=status.HTTP_201_CREATED)
def create_user(user:schemas.CreateUser, db:Session = Depends(get_db)):
    hashed_password = utils.hashing(user.password)
    api_key = utils.generate_api_key()
    hashed_api_key = utils.hash_api_key(api_key)

    new_user = models.Users(api_key=hashed_api_key, hashed_password=hashed_password,
                            email=user.email)

    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
        return {"email": user.email,
                "api_key": api_key,
                "Imp Note": "Note down api-key, it won't be shown again!!!"}

    except IntegrityError:
        # Rollback the failed transaction so the session can be used again
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with that email already exists."
        )

@router.post("/regenerate-key",status_code=status.HTTP_201_CREATED)
def regenerate_api_key(user:schemas.CreateUser, db:Session = Depends(get_db)):
    db_user_row = db.query(models.Users).filter(models.Users.email == user.email).first()
    if not db_user_row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid credentials")

    if utils.verify(user.password, db_user_row.hashed_password):
        api_key = utils.generate_api_key()
        hashed_api_key = utils.hash_api_key(api_key)
        db_user_row.api_key = hashed_api_key

        db.commit()
        db.refresh(db_user_row)

        return {"email": user.email,
                "api_key": api_key,
                "Imp Note": "Note down api-key, it won't be shown again!!!"}

    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid credentials")

@router.delete("/me",status_code=status.HTTP_204_NO_CONTENT)
def delete_user(api_key:str = Security(my_key_grabber), db:Session = Depends(get_db)):
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="API-Key Empty")

    hashed_api = utils.hash_api_key(api_key)
    user_query = db.query(models.Users).filter(models.Users.api_key == hashed_api)
    user = user_query.first()

    #not valid api key
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid API-Key")

    user_query.delete(synchronize_session = False)
    db.commit()

    return

@router.get("/me")
def get_user(api_key:str = Security(my_key_grabber),db:Session = Depends(get_db)):
    # not valid api key
    user = utils.get_curr_user(api_key,db)
    return {"email":user.email}

