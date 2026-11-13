"""Проверки парсера каталога books.toscrape.com."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scraper import get_book_data, scrape_books

BOOK_URL = (
    "http://books.toscrape.com/catalogue/"
    "a-light-in-the-attic_1000/index.html"
)

REQUIRED_KEYS = {
    "title",
    "price",
    "rating",
    "stock_quantity",
    "description",
    "product_information",
}

PRODUCT_INFO_KEYS = {
    "UPC",
    "Product Type",
    "Price (excl. tax)",
    "Price (incl. tax)",
    "Tax",
    "Availability",
    "Number of reviews",
}


def test_get_book_data_returns_dict_with_required_keys():
    """Словарь книги содержит нужные поля."""
    data = get_book_data(BOOK_URL)

    assert isinstance(data, dict)
    assert REQUIRED_KEYS <= set(data)
    assert isinstance(data["product_information"], dict)
    assert PRODUCT_INFO_KEYS <= set(data["product_information"])
    assert isinstance(data["stock_quantity"], int)
    assert data["description"]


def test_known_book_title_is_correct():
    """Название известной книги верное."""
    data = get_book_data(BOOK_URL)

    assert data["title"] == "A Light in the Attic"


def test_first_catalogue_page_has_twenty_books():
    """На первой странице каталога 20 книг."""
    books = scrape_books(is_save=False, max_pages=1)

    assert isinstance(books, list)
    assert len(books) == 20
    assert all(isinstance(book, dict) for book in books)
    assert books[0]["title"] == "A Light in the Attic"
