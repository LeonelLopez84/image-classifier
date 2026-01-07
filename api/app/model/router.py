import os
from typing import List

from app import db
from app import settings as config
from app import utils
from app.auth.jwt import get_current_user
from app.model.schema import PredictRequest, PredictResponse
from app.model.services import model_predict
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

router = APIRouter(tags=["Model"], prefix="/model")


@router.post("/predict")
async def predict(file: UploadFile, current_user=Depends(get_current_user)):
    # 1. Validate extension
    if not utils.allowed_file(file.filename):
         raise HTTPException(status_code=400, detail="Invalid file type")

    # 2. Read content and calcualte hash
    file_content = await file.read()

    file_hash = await utils.get_file_hash(file_content)
    
    extension = os.path.splitext(file.filename)[1].lower()
    image_name = f"{file_hash}{extension}"
    
    # 3. save file
    img_path = os.path.join(config.UPLOAD_FOLDER, image_name)
    if not os.path.exists(img_path):
        with open(img_path, "wb") as f:
            f.write(file_content)

    # 4. get prodiction
    prediction, score = await model_predict(image_name)
    
    return PredictResponse(
        success=True, 
        prediction=prediction, 
        score=score, 
        image_file_name=image_name
    )
