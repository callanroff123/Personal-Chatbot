# Import required modules
import requests
from bs4 import BeautifulSoup
from config import URLS


# Scrape context from my website
def load_context():
    context = []
    for url in URLS:
        html = requests.get(url, timeout = 10).text
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        context.append({
            "type": url.split("/")[-1],
            "text": soup.get_text("\n", strip = True)
        })
    return(context)