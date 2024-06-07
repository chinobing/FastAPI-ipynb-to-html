#!/usr/bin/python3
# -*- coding:utf-8 -*-
# __author__ = '__ChinoBing__'

from datetime import datetime
from pydantic import BaseModel


class CreateIpynbData(BaseModel):
    hash_val: str
    title: str
    size: str
    complete: bool = False
    showcode: bool = False

class ReadIpynbData(CreateIpynbData):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
