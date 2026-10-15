from pydantic import BaseModel, Field


class StudentCreate(BaseModel):
    id: str = Field(..., min_length=1, max_length=20, description="学号")
    name: str = Field(..., min_length=1, max_length=50)
    class_name: str = Field(..., min_length=1, max_length=50, alias="className")
    age: int = Field(0, ge=0, le=120)
    score: float = Field(0, ge=0, le=100)

    model_config = {"populate_by_name": True}


class StudentUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    class_name: str = Field(..., min_length=1, max_length=50, alias="className")
    age: int = Field(0, ge=0, le=120)
    score: float = Field(0, ge=0, le=100)

    model_config = {"populate_by_name": True}


class StudentOut(BaseModel):
    id: str
    name: str
    class_name: str = Field(..., serialization_alias="className")
    age: int
    score: float

    model_config = {"from_attributes": True, "populate_by_name": True}


class StatsOut(BaseModel):
    total: int
    class_count: int
    avg_score: float | None
    excellent: int


class ClassesOut(BaseModel):
    classes: list[str]
