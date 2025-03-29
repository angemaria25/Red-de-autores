import os
import requests
import feedparser
import re
from time import sleep
from urllib.parse import quote

query = "deep learning"
max_results = 200
output_folder = "articles_clean"
retry_count = 3


os.makedirs(output_folder, exist_ok=True)

def clean_filename(title):
    """Limpia el título para crear nombres de archivo válidos en Windows"""
    title = re.sub(r'[\\/*?:"<>|\n]', '', title)  
    title = re.sub(r'\s+', ' ', title).strip()     
    title = re.sub(r'[^\w\s-]', '', title)         
    title = re.sub(r'[\x00-\x1f]', '', title)     
    return title[:150]  
def download_pdf(url, path):
    for attempt in range(retry_count):
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                with open(path, 'wb') as f:
                    f.write(response.content)
                return True
        except Exception as e:
            print(f"  Intento {attempt+1} fallido: {str(e)}")
            sleep(delay * (attempt + 1))
    return False

base_url = "http://export.arxiv.org/api/query?"
params = {
    'search_query': f'all:{quote(query)}',
    'start': 0,
    'max_results': max_results,
    'sortBy': 'submittedDate',
    'sortOrder': 'descending'
}

try:
    response = requests.get(base_url, params=params, timeout=30)
    response.raise_for_status()
    feed = feedparser.parse(response.content)
except Exception as e:
    print(f"Error al obtener feed: {str(e)}")
    feed = []

success_count = 0
for entry in feed.entries[:max_results]:
    try:
        if not hasattr(entry, 'title') or not entry.title:
            continue

        clean_title = clean_filename(entry.title)
        pdf_name = f"{clean_title}.pdf"
        pdf_path = os.path.join(output_folder, pdf_name)

        
        if os.path.exists(pdf_path):
            print(f"⏩ Saltando (ya existe): {pdf_name[:60]}...")
            success_count += 1
            continue

        
        pdf_url = next((link.href for link in entry.links if link.get('title') == 'pdf'), None)
        
        if pdf_url:
            if download_pdf(pdf_url, pdf_path):
                success_count += 1
                print(f"✅ [{success_count}/{len(feed.entries)}] {pdf_name[:60]}...")
            else:
                print(f"❌ Fallo al descargar: {pdf_name[:60]}...")
        else:
            print(f"⚠️ Sin enlace PDF: {clean_title[:60]}...")
        
        sleep(delay)
        
    except Exception as e:
        print(f"⚠️ Error procesando entrada: {str(e)}")

print(f"\nDescarga completada. {success_count} papers descargados exitosamente.")
print(f"Ubicación: {os.path.abspath(output_folder)}")