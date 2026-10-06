from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, SignupRequest


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Retrieve a user by normalized email."""
    normalized_email = email.strip().lower()
    result = await db.execute(select(User).where(User.email == normalized_email))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, data: SignupRequest) -> User:
    """Create a new user with a hashed password."""
    normalized_email = data.email.strip().lower()
    user = User(
        name=data.name.strip(),
        email=normalized_email,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, data: LoginRequest) -> Optional[User]:
    """Verify credentials and return user if valid, None otherwise."""
    user = await get_user_by_email(db, data.email)
    if not user:
        return None
    if not verify_password(data.password, user.hashed_password):
        return None
    return user

