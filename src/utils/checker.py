from lxml import etree

def check_version(file_path):
    try:
        tree = etree.parse(str(file_path))
        root = etree.getroot()
        version_str = root.get('version', '2020.0')
        return int(version_str.split('.')[0])
    except Exception:
        return 2020