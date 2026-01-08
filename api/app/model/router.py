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

    filename = getattr(file, "filename", "")
    
    if not utils.allowed_file(filename):
        raise HTTPException(
            status_code=400,
            detail="File type is not supported."
        )

    image_name = await utils.get_file_hash(file)
    
    file_content = await file.read()
    
    img_path = os.path.join(config.UPLOAD_FOLDER, image_name)
    if not os.path.exists(img_path):
        with open(img_path, "wb") as f:
            f.write(file_content)

    # 5. Predicction
    prediction, score = await model_predict(image_name)
    
    return PredictResponse(
        success=True, 
        prediction=prediction, 
        score=round(float(score), 4),
        image_file_name=image_name
    )
