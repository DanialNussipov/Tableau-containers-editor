def generate_tree_text(node: dict, prefix: str = "", is_last: bool = True, is_root: bool = True) -> str:
    """
    Рекурсивно строит текстовое представление иерархии контейнеров.
    """
    # Определяем коннекторы для текущего узла
    if is_root:
        connector = ""
    else:
        connector = "└── " if is_last else "├── "
        
    # Формируем имя узла (тип + ориентация + ID + пользовательское имя, если есть)
    node_type = node.get("type", "unknown")
    param = node.get("param", "")
    name = node.get("name", "")
    node_id = node.get("id", "")
    
    display_name = f"{node_type}"
    if param:
        display_name += f" ({param})"
    display_name += f" [id:{node_id}]"
    if name:
        display_name += f" '{name}'"
        
    # Формируем комментарий с текущими стилями
    styles = node.get("styles", {})
    style_parts = [f"{k}={v}" for k, v in styles.items()]
    comment = f"    # {', '.join(style_parts)}" if style_parts else ""
    
    # Собираем строку текущего узла (с выравниванием комментария)
    current_line = f"{prefix}{connector}{display_name}".ljust(50) + comment + "\n"
    
    # Рекурсивно обрабатываем дочерние элементы
    children = node.get("children", [])
    result = current_line
    
    for index, child in enumerate(children):
        is_last_child = (index == len(children) - 1)
        if is_root:
            child_prefix = prefix
        else:
            child_prefix = prefix + ("    " if is_last else "│   ")
            
        result += generate_tree_text(
            child, 
            prefix=child_prefix, 
            is_last=is_last_child, 
            is_root=False
        )
        
    return result