from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import shutil
from pathlib import Path
# Импортируем наши написанные модули
from src.parser.xml_parser import parse_twb
from src.transformer.modifier import modify_dashboard_styles
from src.utils.formatter import generate_tree_text

app = FastAPI(title="Tableau Style Manager API")

# Папка для временных файлов
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

# Pydantic-схема для запроса на изменение
class ModifyRequest(BaseModel):
    filename: str = Field(..., description="Имя ранее загруженного файла")
    dashboard_name: str = Field(..., description="Имя дашборда")
    zone_ids: List[str] = Field(..., description="Список ID контейнеров")
    inner_padding: Optional[int] = Field(None, description="Inner Padding")
    outer_padding: Optional[int] = Field(None, description="Outer Padding")

@app.post("/upload_text", response_class=PlainTextResponse)
async def upload_file_text_view(file: UploadFile = File(...)):
    """
    Принимает .twb файл и возвращает текстовое дерево с комментариями параметров.
    """
    if not file.filename.endswith('.twb'):
        raise HTTPException(status_code=400, detail="Только файлы .twb поддерживаются")
        
    file_path = TEMP_DIR / file.filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        dashboards_hierarchy = parse_twb(str(file_path))
        
        # Формируем итоговый текстовый документ
        text_output = f"Файл: {file.filename}\n"
        text_output += "=" * 80 + "\n\n"
        
        for dash_name, root_node in dashboards_hierarchy.items():
            text_output += f"Dashboard: {dash_name}\n"
            text_output += generate_tree_text(root_node)
            text_output += "\n" + "-" * 80 + "\n\n"
            
        return text_output
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка парсинга файла: {str(e)}")
    
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Принимает .twb файл, сохраняет его и возвращает древовидную иерархию дашбордов."""
    if not file.filename.endswith('.twb'):
        raise HTTPException(status_code=400, detail="Только файлы .twb поддерживаются")
        
    file_path = TEMP_DIR / file.filename
    
    # Сохраняем загруженный файл
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Парсим структуру
    try:
        dashboards_hierarchy = parse_twb(str(file_path))
        return {
            "filename": file.filename, 
            "dashboards": dashboards_hierarchy
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка парсинга файла: {str(e)}")

@app.post("/modify")
async def modify_file(request: ModifyRequest):
    """Принимает параметры изменений, применяет их к файлу и отдает обновленный .twb."""
    input_path = TEMP_DIR / request.filename
    
    if not input_path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден. Сначала загрузите его через /upload")
        
    output_filename = f"modified_{request.filename}"
    output_path = TEMP_DIR / output_filename
    
    # Применяем изменения
    modify_dashboard_styles(
        input_file_path=str(input_path),
        output_file_path=str(output_path),
        dashboard_name=request.dashboard_name,
        zone_ids=request.zone_ids,
        inner_pad=request.inner_padding,
        outer_pad=request.outer_padding
    )
    
    # Возвращаем файл пользователю как вложение для скачивания
    return FileResponse(
        path=output_path, 
        filename=output_filename,
        media_type='application/xml'
    )