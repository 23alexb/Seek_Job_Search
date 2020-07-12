#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from selenium import webdriver
import bs4
import requests
import requests.exceptions
import pandas as pd
import re

# Create output data frames (two relational tables, URL as shared key)
df_job_details = pd.DataFrame(columns=['URL', 'Job_Title', 'Company'])
df_job_requirements = pd.DataFrame(columns=['URL', 'Sentence'])

# Initialise browser, page iteration, and url list
browser = webdriver.Firefox()
urls = []
i = 1

# For each page of search, collect urls to job ad pages
while True:
    browser.get('https://www.seek.co.nz/python-jobs/in-All-Auckland?page=' + str(i) + '&sortmode=ListedDate')
    # Get list of urls
    urls = urls + [elem.get_attribute('href') for elem in browser.find_elements_by_class_name('_2iNL7wI')]
    i = i + 1
    if len(browser.find_elements_by_class_name('bHpQ-bp')) == 0 : break # If no "NEXT" button on page, don't check next page

# Quit browser and initialise regex for parsing terms from HTML
browser.quit()
term_search_regex = '<[ilp]{1,2}>([^<]*)</[ilp]{1,2}>'

# For each URL, retrieve HTML from page and parse to get job title, company name, and job requirements
for url in urls:
    # Retrieve soup object for web page
    res = requests.get(url)
    try:
        res.raise_for_status()
    except requests.exceptions.HTTPError:
        continue
    soup = bs4.BeautifulSoup(res.text, 'lxml')
    
    # Retrieve job title and company
    job_title = str(soup.find_all('h1')[0].string)
    if len(soup.find_all('span', class_='_3FrNV7v _2QG7TNq E6m4BZb')) != 0:
        company = str(soup.find('span', class_='_3FrNV7v _2QG7TNq E6m4BZb').string)
    else:
        company = ''
    
    # Add job title and company to df_job_details with url as key
    new_row = [url, job_title, company]
    df_job_details.loc[df_job_details.shape[0] + 1] = new_row
    
    # Retrieve element for job description
    jd_elem = soup.find('div', class_='_2e4Pi2B')
    jd_elem = str(jd_elem)
    
    # Remove HTML irrelevant to output
    for regex_term in ['</?strong>', '<a [^>]*>', '</a>', '<div [^>]*>', '</div>', '</?em>', '</?ul>']:
        while re.search(regex_term, jd_elem) is not None:
            remove_string = re.search(regex_term, jd_elem).group(0)
            jd_elem = jd_elem.replace(remove_string, '')
    
    # Extract terms and add to list
    terms_list = []
    while re.search(term_search_regex, jd_elem) is not None:
        terms_list.append(re.search(term_search_regex, jd_elem).groups(0)[0])
        jd_elem = jd_elem.replace(re.search(term_search_regex, jd_elem).group(0), '')
        
    # Add terms to df_job_requirements dataframe with url as key
    for term in terms_list:
        new_row = [url, term]
        df_job_requirements.loc[df_job_requirements.shape[0] + 1] = new_row
        
df_job_details.to_csv('Job Details.csv')
df_job_requirements.to_csv('Job Requirements.csv')
