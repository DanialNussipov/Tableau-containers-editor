from lxml import etree
from pathlib import Path

def _set_format_attr(zone_style, attr_name: str, value: str):
    """Ищет атрибут в <zone-style> и обновляет его. Если нет — создает новый."""
    for fmt in zone_style.findall('format'):
        if fmt.get('attr') == attr_name:
            fmt.set('value', value)
            return
    
    # Если тега <format> с таким атрибутом нет, создаем его
    etree.SubElement(zone_style, 'format', attr=attr_name, value=value)

def modify_dashboard_styles(input_file_path: str, output_file_path: str, dashboard_name: str, zone_ids: list[str], inner_pad: int = None, outer_pad: int = None):
    tree = etree.parse(input_file_path)
    root = tree.getroot()
    modified_count = 0
    
    # Прямой перебор всех дашбордов для 100% надежности
    dashboard_node = None
    for dashboard in root.iter('dashboard'):
        if dashboard.get('name') == dashboard_name:
            dashboard_node = dashboard
            break
            
    if dashboard_node is not None:
        for zone in dashboard_node.iter('zone'):
            if zone.get('id') in zone_ids:
                zone_style = zone.find('zone-style')
                if zone_style is None:
                    zone_style = etree.SubElement(zone, 'zone-style')
                
                if inner_pad is not None:
                    _set_format_attr(zone_style, 'padding', str(inner_pad))
                
                if outer_pad is not None:
                    _set_format_attr(zone_style, 'margin', str(outer_pad))
                    
                modified_count += 1

    tree.write(output_file_path, encoding='utf-8', xml_declaration=True)
    return modified_count


if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent
    input_twb = project_root / "data" / "sample_dashboard.twb"
    output_twb = project_root / "data" / "modified_dashboard.twb"
    
    # ВАЖНО: Замени 'Overview' на реальное имя дашборда из твоего файла
    target_dashboard = "Overview" 
    # ВАЖНО: Укажи ID контейнеров, которые хочешь изменить
    test_zones = ['2', '39']  # Пример ID контейнеров для изменения
    
    if input_twb.exists():
        changed = modify_dashboard_styles(
            input_file_path=str(input_twb), 
            output_file_path=str(output_twb), 
            dashboard_name=target_dashboard,
            zone_ids=test_zones, 
            inner_pad=40,  # Ставим Inner Padding в 40
            outer_pad=20  # Ставим Outer Padding в 20
        )
        print(f"Успешно изменено контейнеров: {changed} на листе '{target_dashboard}'.")
        print(f"Файл сохранен как {output_twb.name}")