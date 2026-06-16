import requests
from bs4 import BeautifulSoup

def clean_html(html_text):
    if not html_text:
        return ""
    soup = BeautifulSoup(html_text, 'html.parser')
    return soup.get_text(separator=" ", strip=True)

def fetch_jobs(query, limit=5):

    url = f"https://sandbox.getonbrd.dev/api/v0/search/jobs?query={query}&per_page={limit}"

    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        jobs = []

        for job in data.get("data", []):
            attributes = job.get("attributes", {})

            raw_description = attributes.get("description", "")
            clean_description = clean_html(raw_description)

            jobs.append({
                "title": attributes.get("title"),
                "url": job.get("links", {}).get("public_url"),
                "description": clean_description
            })

        return jobs
    else:
        print(f"Error al conectar con la API: {response.status_code}")
        return []
    
if __name__ == "__main__":
    print("Buscando las primeras 2 ofertas de 'Python'...")
    ofertas = fetch_jobs("C#", limit=2)

    for i, oferta in enumerate(ofertas, 1):
        print(f"\nOferta {i}:")
        print(f"Título: {oferta['title']}")
        print(f"URL: {oferta['url']}")
        print(f"Descripción: {oferta['description'][:500]}...")  # Mostrar solo los primeros 200 caracteres