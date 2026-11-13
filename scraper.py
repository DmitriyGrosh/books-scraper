"""Парсер каталога books.toscrape.com."""

import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
import schedule
from bs4 import BeautifulSoup

CATALOGUE_URL = "http://books.toscrape.com/catalogue/page-{N}.html"
DATA_PATH = Path("artifacts") / "books_data.txt"
REQUEST_TIMEOUT_SECONDS = 30
_SESSION = requests.Session()


def _fetch_response(url: str) -> requests.Response:
    """Загружает страницу и кодировку.

    Args:
        url (str): абсолютный адрес страницы.

    Returns:
        requests.Response: ответ сервера.
        Текст читается в кодировке страницы.

    Raises:
        requests.RequestException: страница не загрузилась
        после трёх попыток.
    """
    last_error: requests.RequestException | None = None
    for attempt in range(3):
        try:
            response = _SESSION.get(
                url,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.encoding = response.apparent_encoding or "utf-8"
            return response
        except requests.RequestException as error:
            last_error = error
            time.sleep(1 + attempt)
    if last_error is None:
        raise requests.RequestException(
            f"Не удалось загрузить {url}"
        )
    raise last_error


def _parse_stock_quantity(availability_text: str) -> int:
    """Достаёт число книг из строки наличия.

    Args:
        availability_text (str): текст вроде
        «In stock (22 available)».

    Returns:
        int: количество доступных экземпляров.
        0, если числа нет.
    """
    match = re.search(r"(\d+)", availability_text)
    if match is None:
        return 0
    return int(match.group(1))


def get_book_data(book_url: str) -> dict:
    """Собирает данные одной книги.

    Args:
        book_url (str): адрес страницы книги.

    Returns:
        dict: название, цена, рейтинг, количество
        в наличии, описание и все поля таблицы
        Product Information.
    """
    response = _fetch_response(book_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    title = soup.find("h1").get_text(strip=True)
    price = soup.select_one("p.price_color").get_text(strip=True)
    rating_class = soup.select_one("p.star-rating").get("class", [])
    rating = next(
        (name for name in rating_class if name != "star-rating"),
        "",
    )
    availability_text = soup.select_one(
        "p.availability"
    ).get_text(strip=True)
    description = ""
    description_header = soup.find(id="product_description")
    if description_header is not None:
        paragraph = description_header.find_next_sibling("p")
        if paragraph is not None:
            description = paragraph.get_text(strip=True)

    product_information: dict[str, str] = {}
    table = soup.find("table", class_="table")
    if table is not None:
        for row in table.find_all("tr"):
            header = row.find("th")
            value = row.find("td")
            if header is None or value is None:
                continue
            product_information[
                header.get_text(strip=True)
            ] = value.get_text(strip=True)

    return {
        "title": title,
        "price": price,
        "rating": rating,
        "stock_quantity": _parse_stock_quantity(availability_text),
        "description": description,
        "product_information": product_information,
    }


def _page_url(catalogue_url: str, page_number: int) -> str:
    """Подставляет номер страницы в шаблон.

    Args:
        catalogue_url (str): шаблон с маркером {N}.
        page_number (int): номер страницы, начиная с 1.

    Returns:
        str: адрес конкретной страницы каталога.
    """
    return catalogue_url.replace("{N}", str(page_number))


def _book_urls(page_url: str, page_html: str) -> list[str]:
    """Собирает абсолютные ссылки на книги.

    Args:
        page_url (str): адрес страницы каталога.
        База для относительных ссылок.
        page_html (str): HTML этой страницы.

    Returns:
        list[str]: ссылки на страницы книг
        в порядке показа на странице.
    """
    soup = BeautifulSoup(page_html, "html.parser")
    urls: list[str] = []
    for link in soup.select("article.product_pod h3 a"):
        href = link.get("href")
        if not href:
            continue
        urls.append(urljoin(page_url, href))
    return urls


def scrape_books(
    catalogue_url: str = CATALOGUE_URL,
    is_save: bool = False,
    max_pages: int | None = None,
) -> list[dict]:
    """Обходит каталог и собирает данные книг.

    Args:
        catalogue_url (str): шаблон адреса страницы.
        Номер страницы ставится вместо {N}.
        is_save (bool): True — записать результат
        в artifacts/books_data.txt.
        False — файл не создавать и не изменять.
        max_pages (int | None): сколько страниц обойти.
        None — все страницы, пока сайт их отдаёт.

    Returns:
        list[dict]: данные книг в порядке обхода.
        Каждый элемент — результат get_book_data.
    """
    books: list[dict] = []
    page_number = 1
    while True:
        if max_pages is not None and page_number > max_pages:
            break
        page_url = _page_url(catalogue_url, page_number)
        response = _fetch_response(page_url)
        if response.status_code == 404:
            break
        response.raise_for_status()
        book_urls = _book_urls(page_url, response.text)
        if not book_urls:
            break
        for book_url in book_urls:
            books.append(get_book_data(book_url))
        print(
            f"Страница {page_number}: "
            f"собрано {len(book_urls)} книг"
        )
        page_number += 1

    if is_save:
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        DATA_PATH.write_text(
            json.dumps(books, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return books


if __name__ == "__main__":
    schedule.every().day.at("19:00").do(scrape_books, is_save=True)
    while True:
        schedule.run_pending()
        time.sleep(1)
