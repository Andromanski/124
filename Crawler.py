import requests
from bs4 import BeautifulSoup
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_html(url):
    """Получение HTML содержимого по URL с обработкой ошибок."""
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()  # Проверка на успешный ответ
        return response.text
    except requests.RequestException as e:
        logging.error(f"Ошибка при запросе {url}: {e}")
        return ""

def extract_links(html):
    """Извлечение всех ссылок, начинающихся с http."""
    soup = BeautifulSoup(html, 'html.parser')
    links = soup.find_all('a', href=True)
    hrefs = [link['href'] for link in links if link['href'].startswith('http')]
    return hrefs

def is_php_site(url):
    """Проверка, является ли сайт PHP, на основе заголовков или содержимого страницы."""
    try:
        response = requests.get(url, timeout=5)
        if 'php' in response.headers.get('Content-Type', '').lower():
            return True
        # Дополнительная проверка на наличие типичных PHP элементов в HTML
        if 'php' in response.text.lower():
            return True
        return False
    except requests.RequestException as e:
        logging.error(f"Ошибка при проверке {url}: {e}")
        return False

def process_url(url, visited, all_links, to_visit):
    """Обработка одного URL: получение HTML, извлечение ссылок и проверка PHP."""
    if url in visited:
        return
    visited.add(url)
    html = get_html(url)
    if html:
        links = extract_links(html)
        for link in links:
            if link not in all_links and len(all_links) < 200:
                if is_php_site(link):
                    logging.info(f"Найден PHP сайт: {link}")
                    all_links.append(link)
                    to_visit.append(link)
    time.sleep(1)  # Задержка между запросами

def main(start_url):
    """Основная функция для запуска программы."""
    visited = set()
    to_visit = [start_url]
    all_links = []

    with ThreadPoolExecutor(max_workers=5) as executor:  # Пул потоков для параллельной обработки
        futures = []
        while len(all_links) < 200 and to_visit:
            url = to_visit.pop(0)
            futures.append(executor.submit(process_url, url, visited, all_links, to_visit))
            # Обработка завершённых задач
            for future in as_completed(futures):
                future.result()

    # Сохранение найденных PHP-сайтов в файл
    with open('sites.txt', 'w') as file:
        for link in all_links:
            file.write(link + '\n')

    logging.info("Ссылки на PHP-сайты сохранены в файл sites.txt")

if __name__ == "__main__":
    start_url = 'https://example.com'  # Начальный URL
    main(start_url)
