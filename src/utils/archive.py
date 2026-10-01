import zipfile
import os
from pathlib import Path

def extract_twbx(twbx_path: Path, extract_dir: Path) -> Path:
    # Распаковывает .twbx архив во временную папку и возвращает путь к .twb файлу.
    extract_dir = Path(extract_dir)
    with zipfile.ZipFile(twbx_path, 'r') as zip_ref:
        dest = extract_dir.resolve()
        # Защита от zip-slip: ни один путь не должен вылезать за пределы extract_dir
        for member in zip_ref.namelist():
            if not (dest / member).resolve().is_relative_to(dest):
                raise ValueError(f"Небезопасный путь в архиве: {member}")
        zip_ref.extractall(extract_dir)

    # Ищем .twb файл внутри распакованной директории
    for root, _, files in os.walk(extract_dir):
        for file in files:
            if file.endswith('.twb'):
                return Path(root) / file
                
    raise FileNotFoundError("Файл .twb не найден внутри архива .twbx")

def pack_twbx(source_dir: Path, output_twbx_path: Path):
    # Запаковывает содержимое папки обратно в архив .twbx (формат zip).
    with zipfile.ZipFile(output_twbx_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
        for root, _, files in os.walk(source_dir):
            for file in files:
                file_path = Path(root) / file
                # Вычисляем относительный путь, чтобы сохранить структуру папок в архиве
                arcname = file_path.relative_to(source_dir)
                zip_ref.write(file_path, arcname)