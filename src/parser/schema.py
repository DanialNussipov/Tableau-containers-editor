from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ZoneStyleUpdate(BaseModel):
    zone_ids: List[str] = Field(..., description="Список ID контейнеров для изменения")
    inner_padding: Optional[int] = Field(None, description="Внутренний отступ (padding) в пикселях")
    outer_padding: Optional[int] = Field(None, description="Внешний отступ (margin) в пикселях")
    corner_radius: Optional[int] = Field(None, description="Радиус скругления углов (corner-radius) в пикселях")
    border_color: Optional[str] = Field(None, description="Цвет границы(border-color) в #rrggbb формате")
    # Задел на будущее: background_color, border_width и т.д.

class DashboardUpdateRequest(BaseModel):
    dashboard_name: str = Field(..., description="Точное имя дашборда, в котором меняем стили")
    updates: ZoneStyleUpdate

class DashboardHierarchyResponse(BaseModel):
    dashboard_name: str
    hierarchy: Dict[str, Any]