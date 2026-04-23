from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.claude import generate_sales_reply
from core.config import ANTHROPIC_API_KEY, MEMORY_MESSAGE_LIMIT
from db.models import Customer, Memory
from db.session import get_db

router = APIRouter(tags=["chat"])

_ROOT = Path(__file__).resolve().parents[1]


def _load_system_prompt() -> str:
    path = _ROOT / "prompts" / "sales_assistant_system.txt"
    return path.read_text(encoding="utf-8").strip()


class ChatRequest(BaseModel):
    customer_external_id: str = Field(..., min_length=1, max_length=255)
    customer_name: str | None = Field(default=None, max_length=255)
    message: str = Field(..., min_length=1, max_length=8000)


class ChatResponse(BaseModel):
    reply: str
    customer_id: int


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    session: AsyncSession = Depends(get_db),
) -> ChatResponse:
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY is not configured")

    result = await session.execute(
        select(Customer).where(Customer.external_id == body.customer_external_id)
    )
    customer = result.scalar_one_or_none()
    if customer is None:
        customer = Customer(
            external_id=body.customer_external_id,
            name=body.customer_name,
        )
        session.add(customer)
        await session.flush()

    if body.customer_name and customer.name != body.customer_name:
        customer.name = body.customer_name

    memory_result = await session.execute(
        select(Memory)
        .where(Memory.customer_id == customer.id)
        .order_by(Memory.created_at.desc())
        .limit(MEMORY_MESSAGE_LIMIT)
    )
    rows = list(memory_result.scalars().all())
    rows.reverse()

    transcript: list[dict[str, str]] = []
    for row in rows:
        role = row.role
        if role not in ("user", "assistant"):
            continue
        transcript.append({"role": role, "content": row.content})

    transcript.append({"role": "user", "content": body.message})

    system = _load_system_prompt()
    reply = await generate_sales_reply(system=system, messages=transcript)

    session.add(
        Memory(customer_id=customer.id, role="user", content=body.message)
    )
    session.add(Memory(customer_id=customer.id, role="assistant", content=reply))
    await session.commit()

    return ChatResponse(reply=reply, customer_id=customer.id)
