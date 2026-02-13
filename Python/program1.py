import requests
from bs4 import BeautifulSoup
import json

BASE_URL = "https://quotes.toscrape.com/page/{}/"

all_quotes = []

for page in range(1, 11):  # pages 1 to 10
    url = BASE_URL.format(page)
    print(f"Scraping page {page}...")

    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Failed to retrieve page {page}")
        continue

    soup = BeautifulSoup(response.text, "html.parser")
    quotes = soup.find_all("div", class_="quote")

    for quote in quotes:
        text = quote.find("span", class_="text").get_text(strip=True)
        author = quote.find("small", class_="author").get_text(strip=True)
        tags = [tag.get_text(strip=True) for tag in quote.find_all("a", class_="tag")]

        quote_data = {
            "quote": text,
            "author": author,
            "tags": tags
        }

        all_quotes.append(quote_data)

# Save to JSON file
with open("quotes.json", "w", encoding="utf-8") as file:
    json.dump(all_quotes, file, indent=4, ensure_ascii=False)

print("Scraping complete. Data saved to quotes.json")
