import uuid
import shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse, PlainTextResponse, HTMLResponse
from starlette.background import BackgroundTask
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

# Импортируем наши написанные модули
from src.parser.xml_parser import parse_twb
from src.transformer.modifier import modify_dashboard_styles
from src.utils.formatter import generate_tree_text
from src.utils.checker import check_version
from src.utils.archive import pack_twbx, extract_twbx

app = FastAPI(title="Tableau Style Manager API")

# Указываем FastAPI, где искать папки с HTML-шаблонами
templates = Jinja2Templates(directory="src/ui/templates")

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse(request, "index.html")

# Папка для временных файлов
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

# Pydantic-схема для запроса на изменение (без проблемного валидатора)
class ModifyRequest(BaseModel):
    filename: str = Field(..., description="Имя ранее загруженного файла")
    dashboard_name: str = Field(..., description="Имя дашборда")
    zone_ids: List[str] = Field(..., description="Список ID контейнеров")
    inner_padding: Optional[int] = Field(None, description="Inner Padding")
    outer_padding: Optional[int] = Field(None, description="Outer Padding")
    corner_radius: Optional[int] = Field(None, description="Corner Radius")
    border_color: Optional[str] = Field(None, description="Border Color")
    border_style: Optional[Literal['none', 'solid', 'dotted', 'dashed']] = Field(None, description='Border style')
    background_color: Optional[str] = Field(None, description="Background Color")


@app.post("/upload_text", response_class=PlainTextResponse)
async def upload_file_text_view(file: UploadFile = File(...)):
    """
    Принимает .twb и .twbx файлы и возвращает текстовое дерево с комментариями параметров.
    """
    if not file.filename.endswith(('.twb', '.twbx')):
        raise HTTPException(status_code=400, detail="Поддерживаемые файлы только .twb и .twbx")
        
    file_path = TEMP_DIR / file.filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    extract_dir = None    
    try:
        # Если это .twbx -> распаковываем во временную папку
        if file.filename.endswith('.twbx'):
            extract_dir = TEMP_DIR / f"temp_{uuid.uuid4().hex}"
            target_twb_path = extract_twbx(file_path, extract_dir)
        else:
            target_twb_path = file_path

        dashboards_hierarchy = parse_twb(str(target_twb_path))
        
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
    finally:
        if extract_dir and extract_dir.exists():
            shutil.rmtree(extract_dir)
    

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Принимает .twb/.twbx файл, сохраняет его и возвращает древовидную иерархию дашбордов."""
    if not file.filename.endswith(('.twb', '.twbx')):
        raise HTTPException(status_code=400, detail="Поддерживаемые файлы только .twb и .twbx")
        
    file_path = TEMP_DIR / file.filename
    
    # Сохраняем загруженный файл
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    extract_dir = None
    try:
        if file.filename.endswith('.twbx'):
            extract_dir = TEMP_DIR / f"temp_{uuid.uuid4().hex}"
            target_twb_path = extract_twbx(file_path, extract_dir)
        else:
            target_twb_path = file_path

        dashboards_hierarchy = parse_twb(str(target_twb_path))
        return {
            "filename": file.filename, 
            "dashboards": dashboards_hierarchy
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка парсинга файла: {str(e)}")
    finally:
        if extract_dir and extract_dir.exists():
            shutil.rmtree(extract_dir)


@app.post("/modify")
async def modify_file(request: ModifyRequest):
    """Принимает параметры изменений, применяет их к файлу и отдает обновленный .twb(x)."""
    input_path = TEMP_DIR / request.filename
    
    if not input_path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден. Сначала загрузите его через /upload")
        
    output_filename = f"modified_{request.filename}"
    output_path = TEMP_DIR / output_filename
    extract_dir = None

    try:
        if request.filename.endswith('.twbx'):
            # 1. Создаем уникальную директорию для безопасной распаковки
            extract_dir = TEMP_DIR / f"req_{uuid.uuid4().hex}"
            
            # 2. Распаковываем исходный архив
            twb_path = extract_twbx(input_path, extract_dir)
            
            # 3. Проверка версии файла после его распаковки
            current_version = check_version(twb_path)
            if request.corner_radius and request.corner_radius > 0 and current_version < 2026:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Параметр 'corner_radius' не поддерживается (версия Tableau {current_version}, требуется >= 2026). Поставьте значение 0."
                )

            # 4. Применяем стили прямо к извлеченному .twb (перезаписываем его)
            modify_dashboard_styles(
                input_file_path=str(twb_path),
                output_file_path=str(twb_path),
                dashboard_name=request.dashboard_name,
                zone_ids=request.zone_ids,
                inner_pad=request.inner_padding,
                outer_pad=request.outer_padding,
                corner_radius=request.corner_radius,
                border_color=request.border_color,
                border_style=request.border_style,
                background_color=request.background_color
            )
            
            # 5. Собираем всё содержимое обратно в новый .twbx архив
            pack_twbx(extract_dir, output_path)
            media_type = 'application/zip'
        else:
            # Логика для обычного .twb
            current_version = check_version(input_path)
            if request.corner_radius and request.corner_radius > 0 and current_version < 2026:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Параметр 'corner_radius' не поддерживается (версия Tableau {current_version}, требуется >= 2026). Поставьте значение 0."
                )
            
            modify_dashboard_styles(
                input_file_path=str(input_path),
                output_file_path=str(output_path),
                dashboard_name=request.dashboard_name,
                zone_ids=request.zone_ids,
                inner_pad=request.inner_padding,
                outer_pad=request.outer_padding,
                corner_radius=request.corner_radius,
                border_color=request.border_color,
                border_style=request.border_style,
                background_color=request.background_color
            )
            media_type = 'application/xml'
            
        # Возвращаем файл пользователю как вложение для скачивания
        # и удаляем готовый файл с диска после того, как он отправлен.
        return FileResponse(
            path=output_path,
            filename=output_filename,
            media_type=media_type,
            background=BackgroundTask(lambda: output_path.unlink(missing_ok=True))
        )
    finally:
        # Гарантированное удаление временных файлов распаковки
        if extract_dir and extract_dir.exists():
            shutil.rmtree(extract_dir)