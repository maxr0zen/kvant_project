from pydantic import BaseModel
from typing import Optional
from bson import ObjectId

class UserProgress(BaseModel):
    user_id: str
    block_id: int
    task_id: int
    status: str  # "completed", "in_progress", "not_started"

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}