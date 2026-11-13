# books-scraper

Парсер учебного каталога [books.toscrape.com](http://books.toscrape.com).
Скрипт собирает данные всех книг: название, цену, рейтинг, количество
в наличии, описание и поля таблицы Product Information.

## Как запустить

Команды нужно выполнять из корня репозитория.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Собрать каталог и сохранить результат в `artifacts/books_data.txt`:

```bash
python -c "from scraper import scrape_books; res = scrape_books(is_save=True); print(type(res), len(res))"
```

Ежедневный запуск в 19:00. Процесс ждёт в цикле и не завершается сам:

```bash
python scraper.py
```

Тесты:

```bash
pytest tests/test_scraper.py
```

Ноутбук с решением: `notebooks/GROSH_D_A_HW_03_python_ds.ipynb`.

## Библиотеки

- `requests` — загрузка страниц каталога и карточек книг
- `beautifulsoup4` — разбор HTML
- `schedule` — ежедневный запуск парсера в 19:00
- `pytest` — тесты функций парсера

Полный список пакетов окружения, включая зависимости этих библиотек,
записан в `requirements.txt`.
