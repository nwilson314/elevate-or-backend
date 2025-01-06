# app/routers/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from app.db import get_session
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, Token

router = APIRouter()

# This param tells FastAPI where the user would normally go to get a token.
# We won't fully rely on tokenUrl, but it's recommended to use "/auth/login" or similar.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> User:
    """
    Decodes the JWT token, fetches the user from DB, and returns the User object.
    Raises 401 if token invalid or user not found.
    """
    try:
        user_id = decode_access_token(token)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token or user ID missing.")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token.")

    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User is inactive.")
    return user


@router.post("/register", response_model=Token)
def register_user(user_data: UserCreate, session: Session = Depends(get_session)):
    # Check if email already in use
    existing_user = session.exec(select(User).where(User.email == user_data.email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered."
        )

    # Create user
    new_user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    # Generate JWT
    access_token = create_access_token(subject=str(new_user.id))
    return Token(access_token=access_token)


@router.post("/login", response_model=Token)
def login_user(login_data: UserLogin, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == login_data.email)).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    access_token = create_access_token(subject=str(user.id))
    return Token(access_token=access_token)


@router.post("/logout")
def logout_user():
    """
    With JWT, "logout" is effectively handled on the client (discarding the token).
    If you want server-side revocation, you'd store used tokens in a blacklist.
    """
    return {"message": "Logout successful."}


@router.get("/me")
def read_current_user(current_user: User = Depends(get_current_user)):
    """
    Protected route example. We retrieve the user from the token using get_current_user.
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "created_at": current_user.created_at,
        "is_active": current_user.is_active,
        "is_superuser": current_user.is_superuser,
    }
