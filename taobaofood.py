# auth: c_tob

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import re
from pyquery import PyQuery as pq
from config import *
import pymongo

client = pymongo.MongoClient(MONGO_URL, connect=False)
db = client[MONGO_DB]

chrome_path = r"D:\webdriver\chromedriver\chromedriver.exe"
# phantomjs_path = r'D:\webdriver\phantomjs\bin\phantomjs.exe'

browser = webdriver.Chrome(chrome_path)
# browser = webdriver.PhantomJS(executable_path=phantomjs_path, service_args=SERVICE_ARGS)
wait = WebDriverWait(browser, 10)
# browser.set_window_size(1400, 900)


def search():
    print('正在搜索')
    try:
        browser.get("https://s.taobao.com")

        input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#q"))
            )
        input.clear()
        input.send_keys(KEYWORD)

        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#J_SearchForm > div > div.search-button > button'))
        )
        submit.click()
        total = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.total')))
        return total[0].text
    except TimeoutException:
        return search()


def next_page(page_num):
    print('正在翻页', page_num)
    try:
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > div.form > input"))
        )
        input.clear()
        input.send_keys(page_num)

        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit'))
        )
        submit.click()
        wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > ul > li.item.active > span'), str(page_num))
        )
        parse_page_products()

    except TimeoutException:
        next_page(page_num)


def parse_page_products():
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-itemlist .items .item')))
    html = browser.page_source
    doc = pq(html)
    items = doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        product = {
            'title': item.find('.title').text(),
            'src': item.find('.pic .img').attr('src'),
            'price': item.find('.price').text(),
            'deal': item.find('.deal-cnt').text()[:-3],
            'shopname': item.find('.shopname').text(),
            'location': item.find('.location').text()
        }
        # print(product)
        save_to_mongo(product)


def save_to_mongo(items):
    try:
        if db[MONGO_TABLE].insert(items):
            print('存储到mongodb成功！', items)
    except Exception as e:
        print(e, items)


def main():
    try:
        text = search()
        pattern = re.compile(r'(\d+)')
        total = int(re.search(pattern, text).group(1))
        for i in range(1, total+1):
            next_page(i)

    except Exception as e:
        print(e)

    finally:
        browser.close()


if __name__ == "__main__":
    main()