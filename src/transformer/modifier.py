from lxml import etree
from pathlib import Path

def _set_format_attr(zone_style, attr_name: str, value: str):
    # Ищет атрибут в <zone-style> и обновляет его. Если нет — создает новый.
    # 1. Проходим по всем вложенным тегам внутри zone_style
    for fmt in zone_style:
        if fmt.get('attr') == attr_name:
            fmt.set('value', value)
            return
        
    # 2. Если атрибут не найден, определяем правильное имя тега для создания
    if attr_name == 'corner-radius':
        tag_name = '_.fcp.DashboardRoundedCorners.true...format'
    else:
        tag_name = 'format'        
        
    # 3. Создаем нужный тег
    etree.SubElement(zone_style, tag_name, attr=attr_name, value=value)

def modify_dashboard_styles(input_file_path: str, 
                            output_file_path: str, 
                            dashboard_name: str, 
                            zone_ids: list[str],
                            inner_pad: int = None,
                            outer_pad: int = None, 
                            corner_radius: int = None, 
                            border_color: str = None,
                            border_style: str = None
                            ):
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

                if corner_radius is not None:
                    _set_format_attr(zone_style, 'corner-radius', str(corner_radius))

                if border_color is not None:
                    _set_format_attr(zone_style, 'border-style', 'solid')
                    _set_format_attr(zone_style, 'border-color', str(border_color))

                if border_style is not None:
                    _set_format_attr(zone_style, 'border-style', str(border_style))

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
            outer_pad=20,  # Ставим Outer Padding в 20
            corner_radius=15, # Ставим Corner Radius в 15
            border_color='#000000',# Ставим черный Border Color
            border_style='solid' # Ставим непрерывную линию границы 
        )
        print(f"Успешно изменено контейнеров: {changed} на листе '{target_dashboard}'.")
        print(f"Файл сохранен как {output_twb.name}")