import re
import os
import time
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By



def extract_product_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.readlines()
    
    product_data = {}
    for line in content:
        # 使用正则表达式分割每行的产品型号和 ASIN
        match = re.split(r'[：:,，]', line.strip())
        if len(match) == 2:
            product_name, asin = match
            product_data[product_name.strip()] = asin.strip()
    
    return product_data


def extract_info(driver):
    # 提取评分信息
    try:
        rating_element = driver.find_element(By.XPATH, '//span[@data-hook="rating-out-of-text"]')
        rating = float(rating_element.text.replace("星，共", "").split(" ")[0])
    except Exception as e:
        rating = None
        print(f"Error extracting rating: {e}")

    # 提取总评分和带评论数量
    try:
        review_summary_element = driver.find_element(By.XPATH, '//div[@data-hook="cr-filter-info-review-rating-count"]')
        review_summary = review_summary_element.text.split(", ")
        total_reviews = int(review_summary[0].split(" ")[0].replace(',', ''))
        with_comment_reviews = int(review_summary[1].split(" ")[0].replace(',', ''))
    except Exception as e:
        total_reviews = None
        with_comment_reviews = None
        print(f"Error extracting review summary: {e}")

    return total_reviews, with_comment_reviews, rating


def save_result(results):
    five_to_one = ['五', '四', '三', '二', '一']
    save_lines = []
    fix_cols = ['总评数']+five_to_one+['总显评数']+five_to_one+['显示评分']
    all_counts, display_counts = [], []
    last_rate = 0.0
    for i, r in enumerate(results):
        if i % 6 == 0:
            if i != 0:
                save_lines.append(",".join(all_counts+display_counts+[last_rate]))
            save_lines.append(r[0]+','*11)
            save_lines.append(",".join(fix_cols))
            all_counts, display_counts = [], []
    
        all_counts.append(str(r[2]))
        display_counts.append(str(r[3]))
        last_rate = str(r[4])

    save_lines.append(",".join(all_counts+display_counts+[last_rate]))

    now = datetime.datetime.now()
    if not os.path.exists('./results'):
        os.mkdir('./results')
    file = f'./results/{now.year}_{now.month}_{now.day}.csv'
    save_lines = [l+'\n' for l in save_lines]
    with open(file, 'w', encoding='utf-8-sig') as f:
        f.writelines(save_lines)


if __name__ == '__main__':

    ratings = ['all_stars', 'five_star', 'four_star', 'three_star', 'two_star', 'one_star']
    product_data = extract_product_data('asins.txt')

    browser = webdriver.Chrome()

    results = []
    for product, asin in product_data.items():
        for rating in ratings:
            url = f'https://www.amazon.co.jp/product-reviews/{asin}/ref=cm_cr_arp_d_viewopt_sr?ie=UTF8&filterByStar={rating}&reviewerType=all_reviews&pageNumber=1#reviews-filter-bar'

            browser.get(url)

            time.sleep(1)
            total_reviews, with_comment_reviews, rating = extract_info(browser)
            print(f"Rating: {rating}, Total Reviews: {total_reviews}, With Comment Reviews: {with_comment_reviews}")
            results.append((product, asin, total_reviews, with_comment_reviews, rating))
    
    browser.quit()

    save_result(results)
