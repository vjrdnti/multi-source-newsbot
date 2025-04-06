from flask import Flask, request, jsonify
import nltk
import os
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk import pos_tag
import urllib.parse
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from flask_cors import CORS


LOG_FILE = "scraped_data.txt"

def save_to_file(text: str):
    """Append text to a file."""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")

def clear_file():
    """Clear the content of the file."""
    open(LOG_FILE, "w", encoding="utf-8").close()

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')

SPLASH_URL = "http://localhost:8050/render.html"

#chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  #no gui
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

app = Flask(__name__)

def process_query(query):
    tokenz = word_tokenize(query)
    sw = set(stopwords.words('english')) | {"news", "latest", "summary", "about", "give", "me", "why", "what", "when"}
    tokens_no_stopwords = [word for word in tokenz if word.lower() not in sw]
    #tagged_tokens = pos_tag(tokens_no_stopwords)
    #noun_tokens = [word for word, tag in tagged_tokens if tag.startswith('NN')]
    #noun_bigrams = []
    #for i in range(len(noun_tokens)-1, 0, -1):
    #    noun_bigrams.append(noun_tokens[i-1] + ' ' + noun_tokens[i])

    return ' '.join(tokens_no_stopwords)  

def fetch_news(query):
    corrected_query = urllib.parse.quote(query)
    rss_url = f'https://news.google.com/rss/search?q={corrected_query}&hl=en-IN&gl=IN&ceid=IN:en'
    feed = feedparser.parse(rss_url)
    meta_data = []
    for entry in feed.entries:
        row = {
            'query': query,
            'title': entry.title,
            'link': entry.link,
            'published': entry.published,
            'published_parsed': datetime(*entry.published_parsed[:6])
        }
        meta_data.append(row)
    meta_data.sort(key=lambda x: x['published_parsed'], reverse=True)
    return meta_data[0:8]

def scrape_news(news_list):
    driver = webdriver.Chrome(options=chrome_options)
    scraped_data = []
    for news in news_list:
        parts = news['title'].split(' - ')
        source = parts[1] if len(parts) > 1 else news['title'] #if no '-' use the full title.
        url = news["link"]
        if not url:
            print(f"Skipping {source}: no link")
            continue
        print(f"Visiting {source}: {url}")
        try:
            driver.get(url)
            time.sleep(2)
            final_url = driver.current_url
            print(f"Redirected to: {final_url}")
            driver.get(final_url)
            time.sleep(3)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
            content = " ".join(paragraphs) if paragraphs else "No content found."
            if len(content)>750:
                scraped_data.append({
		            "source": source,
		            "content": content,
		            "final_url": final_url,
		            "all": soup.get_text()
		            })
        except Exception as e:
            print(f"Error scraping {source}: {e}")
    driver.quit()
    return scraped_data


"""
def scrape_news(news_list):
  scraped_data = []
  for news in news_list:
    if len(scraped_data)>5:
      break
    parts = news['title'].split(' - ')
    source = parts[1] if len(parts) > 1 else news['title']
    url = news["link"]
    if not url:
      continue
    try:
      response = requests.get(SPLASH_URL, params = {'url': url, 'timeout':5})
      final_url = response.url
      response = requests.get(SPLASH_URL, params = {'url':final_url, 'timeout':5})
      soup = BeautifulSoup(response.text, "html.parser")
      paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
      content = " ".join(paragraphs) if paragraphs else "No content found."
      if len(content)>750:
        scraped_data.append({
            "source": source,
            "content": content,
            "final_url": final_url,
            "all": soup.get_text()
        })
        print("TEST_BLOCK\n") 
        print(scraped_data) 
    except Exception as e:
      print(f"Error scraping {source}: {e}")
    return scraped_data
"""

def dummy_summarize(article):
    # common container names like "content" nahi toh "all"
    text = article["content"] +"\n***********\n"+ article["all"]
    sentences = sent_tokenize(text)
    summary = " ".join(sentences[:5])
    return summary

@app.route('/summarize', methods=['POST'])
def summarize_endpoint():

    data = request.get_json()
    #expect json argument with a "query" key.
    query = data.get("query")
    if not query:
        return jsonify({"error": "No query provided"}), 400

    #query processing
    query_processed = process_query(query)
    news_results = []
    rows = fetch_news(query_processed)
    for r in rows:
       # Avoid duplicate news based on title
      if r['title'] not in [nr['title'] for nr in news_results]:
        news_results.append(r)
        print(r)
    #scraping
    articles = scrape_news(news_results)
    #dummy summarization.
    summaries = []
    for article in articles:
        summary_text = dummy_summarize(article)
        row = {
            "source": article["source"],
            "final_url": article["final_url"],
            "summary": summary_text
        }
        summaries.append(row)
        
    return jsonify(summaries)

if __name__ == '__main__':
    CORS(app)
    app.run(debug=True)

