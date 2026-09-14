from lxml import etree
from pprint import pprint

def parse_zone(zone_element, parent_id=None):
    """
    Рекурсивно парсит тег <zone> и его дочерние элементы.
    """
    zone_id = zone_element.get('id')
    zone_type = zone_element.get('type-v2')
    name = zone_element.get('name', '')  # Имя есть не у всех зон, берем пустое если нет
    param = zone_element.get('param', '') 
    
    
    # 1. Собираем стили контейнера (margin, padding, border и т.д.)
    styles = {}
    zone_style = zone_element.find('zone-style')
    if zone_style is not None:
        for fmt in zone_style.findall('format'):
            attr = fmt.get('attr')
            value = fmt.get('value')
            if attr and value is not None:
                styles[attr] = value

    # 2. Формируем узел
    node = {
        "id": zone_id,
        "type": zone_type,
        "name": name,
        "param": param,
        "parent_id": parent_id,
        "styles": styles,
        "children": []
    }

    # 3. Ищем вложенные контейнеры <zone>
    for child in zone_element:
        if child.tag == 'zone':
            child_node = parse_zone(child, parent_id=zone_id)
            node["children"].append(child_node)

    return node

def parse_twb(file_path):
    """
    Открывает .twb файл и извлекает иерархию зон с привязкой к именам дашбордов.
    """
    tree = etree.parse(file_path)
    root = tree.getroot()
    
    dashboards = {}
    
    # Ищем основной блок со всеми дашбордами
    dashboards_node = root.find('dashboards')
    if dashboards_node is not None:
        for dashboard in dashboards_node.findall('dashboard'):
            dash_name = dashboard.get('name')
            
            # Ищем блок зон внутри конкретного дашборда
            zones_node = dashboard.find('zones')
            if zones_node is not None:
                # Берем первую корневую зону (обычно это Tiled)
                root_zone = zones_node.find('zone')
                if root_zone is not None:
                    dashboards[dash_name] = parse_zone(root_zone)
                    
    return dashboards


if __name__ == "__main__":
    from pathlib import Path
    from pprint import pprint

    project_root = Path(__file__).parent.parent.parent
    test_file = project_root / "data" / "sample_dashboard.twb"
    
    if test_file.exists():
        dashboards_dict = parse_twb(str(test_file))
        
        # Выводим список всех найденных дашбордов
        print("Найдены дашборды:")
        for name in dashboards_dict.keys():
            print(f"- {name}")
            
        # Пример: как получить иерархию конкретного дашборда
        # Замени 'Overview' на реальное имя дашборда из твоего файла
        target_dashboard = 'Overview' 
        
        if target_dashboard in dashboards_dict:
            print(f"\nСтруктура дашборда '{target_dashboard}':")
            # depth=None покажет всю глубину вложенности без [...]
            pprint(dashboards_dict[target_dashboard], depth=None) 
        else:
            print(f"\nДашборд '{target_dashboard}' не найден в словаре. Выбери из списка выше.")