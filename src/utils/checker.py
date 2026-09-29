from lxml import etree

def check_version(file_path):
    try:
        tree = etree.parse(str(file_path))
        root = tree.getroot()
        
        # Сначала пытаемся достать реальную версию из source-build (например, "2026.1.0...")
        build_str = root.get('source-build')
        if build_str:
            # Берем всё до первой точки, получаем 2026
            return int(build_str.split('.')[0])
            
        # Если атрибута нет (очень старые файлы), падаем на запасной вариант
        version_str = root.get('version', '2020.0')
        return int(version_str.split('.')[0])
        
    except Exception as e:
        print(f"Ошибка при парсинге версии из {file_path}: {e}")
        return 2020