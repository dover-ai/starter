"""CRUD для примерной сущности.

Важная деталь: каждый запрос ограничен объектами текущего пользователя.
Проверка владения выполняется в запросе к БД, а не после выборки —
так исключён доступ к чужим записям по прямому идентификатору.
"""

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.deps import CurrentUser, DbSession
from app.models import Item
from app.schemas import ItemCreate, ItemRead, ItemUpdate

router = APIRouter(prefix="/items", tags=["items"])


def _get_owned_item(db: DbSession, item_id: int, owner_id: int) -> Item:
    item = db.scalar(select(Item).where(Item.id == item_id, Item.owner_id == owner_id))
    if item is None:
        # 404, а не 403: существование чужой записи не подтверждается.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запись не найдена")
    return item


@router.get("", response_model=list[ItemRead])
def list_items(
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[Item]:
    stmt = (
        select(Item)
        .where(Item.owner_id == current_user.id)
        .order_by(Item.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt))


@router.post("", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
def create_item(payload: ItemCreate, db: DbSession, current_user: CurrentUser) -> Item:
    item = Item(**payload.model_dump(), owner_id=current_user.id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{item_id}", response_model=ItemRead)
def get_item(item_id: int, db: DbSession, current_user: CurrentUser) -> Item:
    return _get_owned_item(db, item_id, current_user.id)


@router.patch("/{item_id}", response_model=ItemRead)
def update_item(
    item_id: int, payload: ItemUpdate, db: DbSession, current_user: CurrentUser
) -> Item:
    item = _get_owned_item(db, item_id, current_user.id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: DbSession, current_user: CurrentUser) -> None:
    item = _get_owned_item(db, item_id, current_user.id)
    db.delete(item)
    db.commit()
