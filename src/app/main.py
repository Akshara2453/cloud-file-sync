from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import io
import os
from db import get_session, init_db
from storage import Storage
from models import FileMetadata
from sqlalchemy import select
from datetime import datetime

app = FastAPI()
s3 = Storage()

@app.on_event("startup")
async def startup():
    # async DB init that waits/retries until the DB is ready
    await init_db()

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    contents = await file.read()
    filename = file.filename

    uploaded_at = datetime.utcnow().isoformat()
    s3_key = f"{filename}-{int(datetime.utcnow().timestamp())}"

    # upload to S3
    s3.upload_bytes(contents, s3_key, file.content_type)

    # record metadata in DB, increment version if file path/name exists
    async with get_session() as session:
        existing = await session.execute(select(FileMetadata).where(FileMetadata.filename == filename))
        existing_row = existing.scalars().first()
        version = 1 if not existing_row else existing_row.version + 1

        meta = FileMetadata(filename=filename, s3_key=s3_key, uploaded_at=datetime.utcnow(), version=version)
        session.add(meta)
        await session.commit()
        await session.refresh(meta)

    return {"id": meta.id, "filename": meta.filename, "version": meta.version}

@app.get("/files")
async def list_files():
    async with get_session() as session:
        result = await session.execute(select(FileMetadata))
        rows = result.scalars().all()
    return [{"id": r.id, "filename": r.filename, "uploaded_at": r.uploaded_at.isoformat(), "version": r.version} for r in rows]

@app.get("/files/{file_id}/download")
async def download(file_id: int):
    async with get_session() as session:
        result = await session.execute(select(FileMetadata).where(FileMetadata.id == file_id))
        row = result.scalars().first()
        if not row:
            raise HTTPException(status_code=404, detail="File not found")
    stream = s3.download_stream(row.s3_key)
    return StreamingResponse(stream, media_type="application/octet-stream", headers={"Content-Disposition": f"attachment; filename={row.filename}"})