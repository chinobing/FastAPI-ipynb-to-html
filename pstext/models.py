#!/usr/bin/python3
# -*- coding:utf-8 -*-
# __author__ = '__ChinoBing__'
from sqlalchemy import Column, String, Integer, Boolean, DateTime, func


from .database import Base

class IPYNBHTML(Base):
    __tablename__ = 'ipynbhtml'  # database name

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hash_val = Column(String(100), nullable=False, comment='hash_val')
    title = Column(String(100), unique=True, nullable=False, comment='name')
    size = Column(String(100), comment='size')

    created_at = Column(DateTime, server_default=func.now(), comment='created_at')
    complete = Column(Boolean, default=False, comment='status')
    showcode = Column(Boolean, default=False, comment='showcode')

    #the way to display data after
    def __repr__(self):
        return f'{self.title}_{self.size}'
