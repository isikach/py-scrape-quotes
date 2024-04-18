import csv
from dataclasses import dataclass

import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup


BASE_URL = "https://quotes.toscrape.com/page/"

@dataclass
class Quote:
    text: str
    author: str
    tags: list[str]

all_quotes = []

def parse_single_quote(soup: BeautifulSoup) -> Quote:
    return Quote(
        text=soup.select_one(".text").text.strip(),
        author=soup.select_one(".author").text.strip(),
        tags=[tag.text.strip() for tag in soup.select(".tags > a.tag")],
    )

# def pages_counter() -> int:
#     page_counter = 1
#     next_page = True
#     while next_page:
#         page = requests.get(BASE_URL + f"{page_counter}/").content
#         soup = BeautifulSoup(page, "html.parser")
#         next_page = soup.select_one(".next")
#         page_counter += 1
#     return page_counter

async def pages_counter() -> int:
    page_counter = 1
    next_page = True
    async with aiohttp.ClientSession() as session:
        while next_page:
            url = BASE_URL + f"{page_counter}/"
            async with session.get(url, ssl=False) as response:
                page_content = await response.content.read()
                soup = BeautifulSoup(page_content, "html.parser")
                next_page = soup.select_one(".next")
                page_counter += 1
    return page_counter

async def get_page_data(session, page):
    url = BASE_URL + f"{page}/"
    async with session.get(url, ssl=False) as response:
        response = await response.content.read()
        soup = BeautifulSoup(response, "html.parser")
        quotes = soup.select(".quote")
        for q in quotes:
            all_quotes.append(parse_single_quote(q))
        print(f"INFO: page {page} finished")

async def gather_data():
    async with aiohttp.ClientSession() as session:
        tasks = []
        last_page_number = await pages_counter()
        for page in range(1, last_page_number):
            tasks.append(asyncio.create_task(get_page_data(session, page)))
        await asyncio.gather(*tasks)


async def main(output_csv_path: str):
    await gather_data()
    with open(output_csv_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Text", "Author", "Tags"])
        for quote in all_quotes:
            writer.writerow([quote.text, quote.author, ', '.join(quote.tags)])


if __name__ == "__main__":
    asyncio.run(main("quotes.csv"))
