# main.py

from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from .database import engine, SessionLocal, Base
from .models import User, UserProfile
from pydantic import BaseModel
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta

# FastAPI instance
app = FastAPI()

# Secret key for JWT token (replace with a secure random key in production)
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models
class UserCreate(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    phone_number: str
    qualification: str
    gender: str
    country: str

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Hashing passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Function to create JWT token
def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Route for user signup
@app.post("/signup/")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = pwd_context.hash(user.password)
    
    # Create User instance
    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    
    # Create UserProfile instance
    db_profile = UserProfile(
        first_name=user.first_name,
        last_name=user.last_name,
        phone_number=user.phone_number,
        qualification=user.qualification,
        gender=user.gender,
        country=user.country,
        user=db_user  # Link UserProfile to User
    )
    db.add(db_profile)
    
    db.commit()
    db.refresh(db_user)
    
    return {"message": "User created successfully"}

# Route for user login and token generation
@app.post("/login/", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not pwd_context.verify(user.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    # Generate JWT token
    access_token_expires = timedelta(minutes=30)  # Token expiration time
    access_token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )
    
    
    return {"access_token": access_token, "token_type": "bearer"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
