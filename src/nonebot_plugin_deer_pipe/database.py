import uuid

from .constants import DATABASE_URL

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import Field, SQLModel, delete, select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Sequence


# Model
class User(SQLModel, table=True):
  id: str = Field(primary_key=True)
  year: int
  month: int

class UserDeer(SQLModel, table=True):
  id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
  user_id: str  = Field(index=True)
  day: int
  count: int    = 0

# Async engine
engin: AsyncEngine = create_async_engine(DATABASE_URL, echo=True)
initialized: bool = False

# Attendance
async def attend(now: datetime, user_id: str) -> dict[int, int]:
  global initialized
  if not initialized:
    initialized = True
    async with engin.begin() as conn:
      await conn.run_sync(SQLModel.metadata.create_all)

  async with AsyncSession(engin) as session:
    user: User | None = (
      await session.exec(select(User).where(User.id == user_id))
    ).one_or_none()

    if user == None:
      user = User(id=user_id, year=now.year, month=now.month)
      session.add(user)

    if user.year != now.year or user.month != now.month:
      await session.exec(delete(UserDeer).where(UserDeer.user_id == user_id))
      user = User(user_id=user_id, year=now.year, month=now.month)
      session.add(user)

    user_deer: Sequence[UserDeer] = (
      await session.exec(select(UserDeer).where(UserDeer.user_id == user_id))
    ).all()

    deer_map: dict[int, int] = dict([(i.day, i.count) for i in user_deer])

    if now.day in deer_map:
      deer_map[now.day] += 1
      current: UserDeer = next(filter(lambda x: x.day == now.day, user_deer))
      current.count += 1
      session.add(current)
    else:
      deer_map[now.day] = 1
      session.add(UserDeer(user_id=user.id, day=now.day, count=1))

    await session.commit()
    return deer_map

async def reattend(
  now: datetime,
  day: int,
  user_id: str
) -> tuple[bool, dict[int, int]]:
  global initialized
  if not initialized:
    initialized = True
    async with engin.begin() as conn:
      await conn.run_sync(SQLModel.metadata.create_all)

  async with AsyncSession(engin) as session:
    user: User | None = (
      await session.exec(select(User).where(User.id == user_id))
    ).one_or_none()

    if user == None:
      user = User(id=user_id, year=now.year, month=now.month)
      session.add(user)

    if user.year != now.year or user.month != now.month:
      await session.exec(delete(UserDeer).where(UserDeer.user_id == user_id))
      user = User(user_id=user_id, year=now.year, month=now.month)
      session.add(user)

    user_deer: Sequence[UserDeer] = (
      await session.exec(select(UserDeer).where(UserDeer.user_id == user_id))
    ).all()

    deer_map: dict[int, int] = dict([(i.day, i.count) for i in user_deer])

    if day in deer_map:
      await session.commit()
      return (False, deer_map)

    deer_map[day] = 1
    session.add(UserDeer(user_id=user.id, day=day, count=1))
    await session.commit()
    return (True, deer_map)
