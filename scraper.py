from bs4 import BeautifulSoup
import requests


def parser_pravda_news():
  url = "https://www.pravda.com.ua/news/"
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }

  try:
    response = requests.get(url, headers=headers, timeout=10)
  except requests.RequestException as error:
    print(f"Error retrieving the page: {error}")
    return []

  if response.status_code != 200:
    print(f"Error retrieving the page: {response.status_code}")
    return []

  soup = BeautifulSoup(response.text, "html.parser")
  articles_data = []

  news_items = soup.find_all("div", class_="article_content")
  if not news_items:
    news_items = soup.find_all("div", class_="article_title")
  if not news_items:
    news_items = soup.find_all("h3")

  for item in news_items:
    link_tag = item.find('a')
    if link_tag:
      title = link_tag.get_text(strip=True)
      link = link_tag.get('href', '')

      if link.startswith('/'):
        link = 'https://www.pravda.com.ua' + link

      if 'pravda.com.ua' in link and not any(
          sub in link for sub in ['life.pravda', 'epravda.com.ua']
      ):
        from datetime import date

        news_date = str(date.today())

        if title and not any(d['link'] == link for d in articles_data):
          articles_data.append(
              {'title': title, 'link': link, 'date': news_date}
          )

  return articles_data