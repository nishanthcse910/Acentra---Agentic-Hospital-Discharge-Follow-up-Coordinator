import re
import zipfile
import xml.etree.ElementTree as ET

def extract_text(file_path: str, ext: str) -> str:
    text = ""
    ext = ext.lower()
    try:
        if ext in ['doc', 'docx']:
            # docx is a zip file
            with zipfile.ZipFile(file_path) as docx:
                xml_content = docx.read('word/document.xml')
                tree = ET.fromstring(xml_content)
                for node in tree.iter():
                    if node.tag.endswith('}t') and node.text:
                        text += node.text + " "
        elif ext in ['xls', 'xlsx']:
            # xlsx is a zip file
            with zipfile.ZipFile(file_path) as xlsx:
                xml_content = xlsx.read('xl/sharedStrings.xml')
                tree = ET.fromstring(xml_content)
                for node in tree.iter():
                    if node.tag.endswith('}t') and node.text:
                        text += node.text + " "
        elif ext == 'pdf':
            # rudimentary raw extraction for simple PDFs
            with open(file_path, 'rb') as f:
                content = f.read()
                # Extract printable ascii runs
                matches = re.findall(b'[ -~]{4,}', content)
                text = " ".join([m.decode('ascii', errors='ignore') for m in matches])
        else:
            # literal read
            with open(file_path, 'r', errors='ignore') as f:
                text = f.read()
    except Exception as e:
        print(f"Extraction error: {e}")
        # fallback raw read
        try:
            with open(file_path, 'rb') as f:
                text = str(f.read(), errors='ignore')
        except:
            pass
    return text

def find_patient_mrns(text: str):
    matches = re.findall(r'MRN-[0-9A-Za-z-]+', text, re.IGNORECASE)
    return list(set([m.upper() for m in matches]))
