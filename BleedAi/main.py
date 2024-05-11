import secrets #using to ensure only authorized users access the session
from fastapi import FastAPI, Depends, HTTPException, Header, File, UploadFile
from sqlalchemy.orm import Session

from cachetools import cached, TTLCache
import mediapipe
from PIL import Image,ImageDraw
from io import BytesIO
import numpy as np

from my_package import crud, models, database


app = FastAPI()
cache = TTLCache(maxsize=100, ttl=300)

# Generate a random secret token
SECRET_TOKEN = secrets.token_hex(16)  # Generate a hex token of length 16

# Authorization function to check the token
async def authenticate(token: str = Header(...)):
    if token != SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True

# Dependency to get DB session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Cached versions of CRUD functions
@cached(cache)
@app.post("/users/", response_model=None, status_code=201)
def cached_create_user(db: Session, name: str):
    return crud.create_user(db, name)

@cached(cache)
def cached_update_user(db: Session, user_id: int, new_name: str):
    return crud.update_user(db, user_id, new_name)

@cached(cache)
def cached_delete_user(db: Session, user_id: int):
    return crud.delete_user(db, user_id)

@app.get("/users/{user_id}", response_model=models.User)
def read_user(user_id: int, db: Session = Depends(get_db), authorized: bool = Depends(authenticate)):
    user = crud.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Use the `authenticate` dependency in each endpoint that requires authorization
@app.post("/users/", response_model=models.User)
def create_user(name: str, db: Session = Depends(get_db), authorized: bool = Depends(authenticate)):
    user = cached_create_user(db, name)
    return user

@app.put("/users/{user_id}", response_model=None, status_code=200)
def update_user(user_id: int, new_name: str, db: Session = Depends(get_db), authorized: bool = Depends(authenticate)):
    user = cached_update_user(db, user_id, new_name)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.delete("/users/{user_id}", response_model=None, status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db), authorized: bool = Depends(authenticate)):
    user = cached_delete_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Initialize MediaPipe face detection module
face_mesh = mediapipe.solutions.face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1)

@app.post("/process-image/")
async def process_image(file: UploadFile = File(...)):
    try:
        # Read image file
        content = await file.read()
        image = Image.open(BytesIO(content))
        
        # Convert image to RGB (MediaPipe requires RGB format)
        image_rgb = image.convert("RGB")
        image_np = np.array(image_rgb)
        
        # Perform facial detection and cropping using MediaPipe
        result = face_mesh.process(image_np)
        if result.multi_face_landmarks:
            for face_landmarks in result.multi_face_landmarks:
                # Draw bounding box around the face
                for landmark in face_landmarks.landmark:
                    x, y, _ = image.size
                    x = int(landmark.x * x)
                    y = int(landmark.y * y)
                    draw = ImageDraw.Draw(image)
                    draw.point([x, y], fill=(255, 0, 0))
        
        # Convert processed image back to bytes
        img_byte_array = BytesIO()
        image.save(img_byte_array, format='PNG')
        img_byte_array.seek(0)
        processed_image = img_byte_array.read()
        
        # Return response with processed image
        return {"processed_image": processed_image}
    
    except Exception as e:
        # Handle errors
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")
    
print("x")
