#!/usr/bin/python3
# -*- coding:utf-8 -*-
# __author__ = '__ChinoBing__'
from sqlalchemy.orm import Session
from pstext import models, schemas
from pstext.database import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# def get_audio_segment_data(db:Session, audio_id: int):
#     return db.query(models.Data).filter(models.Data.audio_id == audio_id).all()

def get_ipynb_by_title(db:Session, title: str):
    return db.query(models.IPYNBHTML).filter(models.IPYNBHTML.title == title).first()

def get_hash_val_by_id(db:Session, id: int):
    return db.query(models.IPYNBHTML).filter(models.IPYNBHTML.id == id).first()


def get_data(db: Session, title: str = None, skip : int = 0, limit: int = 10):
    if title:
        return db.query(models.IPYNBHTML).filter(models.IPYNBHTML.title.like('%'+title+'%')).all()
    return db.query(models.IPYNBHTML).order_by(models.IPYNBHTML.created_at.desc()).offset(skip).limit(limit).all()

def create_ipynb_info(db: Session, data : schemas.CreateIpynbData):
    db_ipynb = models.IPYNBHTML(**data)
    db.add(db_ipynb)
    db.commit()
    db.refresh(db_ipynb)
    return db_ipynb

def convert_ipynb(db: Session, ipynb_id: int):
    db_ipynb = db.query(models.IPYNBHTML).filter(models.IPYNBHTML.id == ipynb_id).first()
    if db_ipynb:
        filename = f"{db_ipynb.title}.ipynb"
        showcode = db_ipynb.showcode
        return filename, showcode
    else:
        return None

# update ipynb conversion status
def update_status(ipynb_id: int, hash_val:str, db: Session=next(get_db())):
    db_ipynb = db.query(models.IPYNBHTML).filter(models.IPYNBHTML.id == ipynb_id).first()
    db_ipynb.complete = True
    db_ipynb.hash_val = hash_val
    db.commit()

# update showcode option
def update_showcode_option(ipynb_id: int, showcode:bool, db: Session=next(get_db())):
    db_ipynb = db.query(models.IPYNBHTML).filter(models.IPYNBHTML.id == ipynb_id).first()
    db_ipynb.showcode = showcode
    db.commit()


def delete_ipynb(db: Session, ipynb_id: int):
    db_ipynb = db.query(models.IPYNBHTML).filter(models.IPYNBHTML.id == ipynb_id).first()
    if db_ipynb:
        db.delete(db_ipynb)
        db.commit()

        filename = f"{db_ipynb.title}.ipynb"
        hash_val = db_ipynb.hash_val
        return filename, hash_val
    else:
        return None
