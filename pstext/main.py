#!/usr/bin/python3
# -*- coding:utf-8 -*-
# __author__ = '__ChinoBing__'
import tempfile, hashlib, shutil, json
import os
from pathlib import Path
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, UploadFile, File, status
from fastapi.templating import Jinja2Templates
from pydantic import FilePath
from typing import Dict
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
from fastcore.utils import run, mkdir

from pstext import crud, schemas
from pstext.database import engine, Base, SessionLocal


application = APIRouter()

templates = Jinja2Templates(directory='./pstext/templates')

Base.metadata.create_all(bind=engine)

ipynb_save_path = Path("./ipynb")
ipynb_raw_path = ipynb_save_path / "raw"
ipynb_output_path = ipynb_save_path / "output"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def escape_quarto_comments(lines):
    """Escape comments that don't match Quarto's directive format."""
    for idx, line in enumerate(lines):
        if line.strip().startswith('#|') and ':' not in line:
            lines[idx] = '#' + line
    return lines

# FastAPI BackgroundTasks
def bg_task(file_path: FilePath, ipynb_id: int, showcode: bool):
    """ipynb to html convesion task"""
    hash_val = hashlib.md5(open(file_path,'rb').read()).hexdigest()
    new_path = Path(f'{ipynb_output_path}/{hash_val}')

    # Load the notebook and modify non-compliant Quarto comments
    with open(file_path, 'r', encoding='utf-8') as f:
        notebook_data = json.load(f)
        for cell in notebook_data['cells']:
            if cell['cell_type'] == 'code':
                cell['source'] = escape_quarto_comments(cell['source'])
    
    # Save the modified notebook
    with open(file_path, 'w') as f:
        json.dump(notebook_data, f)
    
    if not new_path.exists():
        mkdir(new_path, exist_ok=True, overwrite=True)
        if showcode == True:
            run(f"quarto render {file_path} --output-dir ../../{new_path} --no-execute --to html --metadata-file nb.yml")
        if showcode == False:
            run(f"quarto render {file_path} --output-dir ../../{new_path} --no-execute --to html --metadata-file nb-hide-code.yml")
        # update conversion status
        crud.update_status(ipynb_id = ipynb_id, hash_val = hash_val)



@application.get("/", response_model=schemas.ReadIpynbData)
async def home(request: Request, title: str = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    data = crud.get_data(db, title=title, skip=skip, limit=limit)

    return templates.TemplateResponse("home.html",
                                      {"request": request,
                                       "data": data})


@application.post("/")
async def upload_files(db: Session = Depends(get_db), file: UploadFile = File(...)):
    filename = file.filename
    title = filename.rsplit('.',1)[0]

    # check if uploading file existed already
    db_title = crud.get_ipynb_by_title(db, title=title)
    if db_title:
        raise HTTPException(status_code=400, detail="ipynb already uploaded")    # 将传过来的文件保存

    # save file
    out_file_path = ipynb_raw_path / file.filename
    async with aiofiles.open(out_file_path, 'wb') as out_file:
        content = await file.read()  # async read
        size = "{}MB".format(round(len(content)/(1024*1024),3))
        await out_file.write(content)  # async write
    data = {
            "hash_val":'',
            "title": title,
            "size": size,
            }
    #create ipynb file info
    result = crud.create_ipynb_info(db = db, data = data)

    return result

@application.get("/convert/{ipynb_id}")
async def convert(background_tasks: BackgroundTasks, request: Request, ipynb_id: int, db: Session = Depends(get_db)):
    filename, showcode = crud.convert_ipynb(db, ipynb_id)
    # title = filename.rsplit('.',1)[0]
    if filename is not None:
        # background tasks for coverting ipynb file
        out_file_path = ipynb_raw_path / filename
        background_tasks.add_task(bg_task, out_file_path, ipynb_id, showcode)

    url = application.url_path_for("home")
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)

#update checkbox option into db
@application.post('/showcode/')
async def showcode(item: Dict[str, str]):
    ipynb_id = int(item['name'])
    if item['checked'] == 'true':
        showcode = True
    else:
        showcode = False

    return crud.update_showcode_option(ipynb_id = ipynb_id, showcode = showcode)

@application.get("/delete/{ipynb_id}")
async def delete(request: Request, ipynb_id: int, db: Session = Depends(get_db)):
    # delete info from sqlite3 and return filename
    filename, hash_val = crud.delete_ipynb(db, ipynb_id)
    if filename is not None:
        os.remove(f'{ipynb_raw_path}/{filename}')
        shutil.rmtree(f'{ipynb_output_path}/{hash_val}')

    url = application.url_path_for("home")
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)

@application.get("/open/{ipynb_id}")
async def open_link(request: Request, ipynb_id: int, db: Session = Depends(get_db)):
    db_ipynb = crud.get_hash_val_by_id(db, ipynb_id)
    hash_val = db_ipynb.hash_val
    title = db_ipynb.title
    open_link = f'../output/{hash_val}/{title}.html'
    return RedirectResponse(open_link)