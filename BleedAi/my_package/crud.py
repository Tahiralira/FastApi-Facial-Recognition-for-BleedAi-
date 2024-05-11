from sqlalchemy.orm import Session
from . import models

def create_user(db: Session, name: str):
    db_user = models.User(name=name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def search_users(db: Session, query: str):
    return db.query(models.User).filter(models.User.name.ilike(f"%{query}%")).all()

def update_user(db: Session, user_id: int, new_name: str):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db_user.name = new_name
        db.commit()
        db.refresh(db_user)
        return db_user

def delete_user(db: Session, user_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
        return db_user

