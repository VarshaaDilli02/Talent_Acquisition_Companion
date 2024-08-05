import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
# from wordcloud import WordCloud
# Developed by dnoobnerd [https://dnoobnerd.netlify.app]    Made with Streamlit
import asyncio
import json
from urllib.parse import urlencode, quote_plus
from typing import List, Dict
from httpx import AsyncClient, Response
from parsel import Selector
from loguru import logger as log
import streamlit as st

# Initialize an async httpx client
client = AsyncClient(
    # Enable HTTP2
    http2=True,
    # Add basic browser-like headers to prevent being blocked
    headers={
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
    },
)

def strip_text(text):
    """Remove extra spaces while handling None values"""
    return text.strip().replace("\n", "") if text is not None else text

def parse_job_search(response: Response) -> List[Dict]:
    """Parse job data from job search pages"""
    selector = Selector(response.text)
    total_results = selector.xpath("//span[contains(@class, 'job-count')]/text()").get()
    total_results = int(total_results.replace(",", "").replace("+", "")) if total_results else None
    data = []
    for element in selector.xpath("//section[contains(@class, 'results-list')]/ul/li"):
        data.append({
            "title": element.xpath(".//div/a/span/text()").get().strip(),
            "company": element.xpath(".//div/div[contains(@class, 'info')]/h4/a/text()").get().strip(),
            "address": element.xpath(".//div/div[contains(@class, 'info')]/div/span/text()").get().strip(),
            "timeAdded": element.xpath(".//div/div[contains(@class, 'info')]/div/time/@datetime").get(),
            "jobUrl": element.xpath(".//div/a/@href").get().split("?")[0],
            "companyUrl": element.xpath(".//div/div[contains(@class, 'info')]/h4/a/@href").get().split("?")[0],
            "salary": strip_text(element.xpath(".//span[contains(@class, 'salary')]/text()").get())
        })
    return {"data": data, "total_results": total_results}

async def scrape_job_search(keyword: str, location: str, max_pages: int = None) -> List[Dict]:
    """Scrape LinkedIn job search"""

    def form_urls_params(keyword, location):
        """Form the job search URL params"""
        params = {
            "keywords": quote_plus(keyword),
            "location": location,
        }
        return urlencode(params)

    first_page_url = "https://www.linkedin.com/jobs/search?" + form_urls_params(keyword, location)
    first_page = await client.get(first_page_url)
    data = parse_job_search(first_page)["data"]
    total_results = parse_job_search(first_page)["total_results"]

    # Get the total number of pages to scrape, each page contains 25 results
    if max_pages and max_pages * 25 < total_results:
        total_results = max_pages * 25
    
    log.info(f"Scraped the first job page, {total_results // 25 - 1} more pages")
    # Scrape the remaining pages concurrently
    other_pages_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?"
    to_scrape = [
        client.get(other_pages_url + form_urls_params(keyword, location) + f"&start={index}")
        for index in range(25, total_results + 25, 25)
    ]
    for response in asyncio.as_completed(to_scrape):
        response = await response
        page_data = parse_job_search(response)["data"]
        data.extend(page_data)

    log.success(f"Scraped {len(data)} jobs from LinkedIn job search")
    return data

async def main_job_search(keyword: str, location: str, max_pages: int):
    job_search_data = await scrape_job_search(keyword, location, max_pages)
    return job_search_data

import nltk
nltk.download('stopwords')
import json
import asyncio
from typing import List, Dict
from httpx import AsyncClient, Response
from parsel import Selector
from loguru import logger as log
import streamlit as st

# Initialize an async httpx client
client = AsyncClient(
    # Enable HTTP2
    http2=True,
    # Add basic browser-like headers to prevent being blocked
    headers={
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
    },
)

def strip_text(text):
    """Remove extra spaces while handling None values"""
    return text.strip().replace("\n", "") if text is not None else text

def parse_jobs(response: Response) -> List[Dict]:
    """Parse job data from job search pages"""
    selector = Selector(response.text)
    total_results = selector.xpath("//span[contains(@class, 'job-count')]/text()").get()
    total_results = int(total_results.replace(",", "").replace("+", "")) if total_results else None
    data = []
    for element in selector.xpath("//section[contains(@class, 'results-list')]/ul/li"):
        data.append({
            "title": element.xpath(".//div/a/span/text()").get().strip(),
            "company": element.xpath(".//div/div[contains(@class, 'info')]/h4/a/text()").get().strip(),
            "address": element.xpath(".//div/div[contains(@class, 'info')]/div/span/text()").get().strip(),
            "timeAdded": element.xpath(".//div/div[contains(@class, 'info')]/div/time/@datetime").get(),
            "jobUrl": element.xpath(".//div/a/@href").get().split("?")[0],
            "companyUrl": element.xpath(".//div/div[contains(@class, 'info')]/h4/a/@href").get().split("?")[0],
            "salary": strip_text(element.xpath(".//span[contains(@class, 'salary')]/text()").get())
        })
    return {"data": data, "total_results": total_results}

async def scrape_jobs(url: str, max_pages: int = None) -> List[Dict]:
    """Scrape LinkedIn job search"""
    first_page = await client.get(url)
    data = parse_jobs(first_page)["data"]
    total_results = parse_jobs(first_page)["total_results"]

    # Get the total number of pages to scrape, each page contain 25 results
    if max_pages and max_pages * 25 < total_results:
        total_results = max_pages * 25
    
    log.info(f"Scraped the first job page, {total_results // 25 - 1} more pages")
    # Scrape the remaining pages using the API
    search_keyword = url.split("jobs/")[-1]
    jobs_api_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/" + search_keyword
    to_scrape = [
        client.get(jobs_api_url + f"&start={index}")
        for index in range(25, total_results + 25, 25)
    ]
    for response in asyncio.as_completed(to_scrape):
        response = await response
        page_data = parse_jobs(response)["data"]
        data.extend(page_data)

    log.success(f"Scraped {len(data)} jobs from LinkedIn company job pages")
    return data

async def main_jobs(url: str, max_pages: int):
    job_search_data = await scrape_jobs(url, max_pages)
    return job_search_data

###### Packages Used ######
import streamlit as st # core package used in this project
import pandas as pd
import base64, random
import time,datetime
import pymysql
import os
import socket
import platform
import geocoder
import secrets
import io,random
import plotly.express as px # to create visualisations at the admin session
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
# libraries used to parse the pdf files
from pyresparser import ResumeParser
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import TextConverter
from streamlit_tags import st_tags
from PIL import Image
# pre stored data for prediction purposes
import streamlit as st
import asyncio
import json
import pandas as pd
import csv
from typing import List, Dict
from httpx import AsyncClient, Response
from parsel import Selector
from loguru import logger as log

from Courses import ds_course,web_course,android_course,ios_course,uiux_course,resume_videos,interview_videos
import nltk
nltk.download('stopwords')
import jmespath
import asyncio
import json
from typing import List, Dict
from httpx import AsyncClient, Response
from parsel import Selector
from loguru import logger as log
import streamlit as st

# Initialize an async httpx client
client = AsyncClient(
    # Enable HTTP2
    http2=True,
    # Add basic browser-like headers to prevent being blocked
    headers={
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
    },
    follow_redirects=True
)

def strip_text(text):
    """Remove extra spaces while handling None values"""
    return text.strip() if text is not None else text

def parse_company(response: Response) -> Dict:
    """Parse company main overview page"""
    assert response.status_code == 200, "Request is blocked, use the ScrapFly codetabs"
    selector = Selector(response.text)
    script_data = json.loads(selector.xpath("//script[@type='application/ld+json']/text()").get())
    script_data = jmespath.search(
        """{
        name: name,
        url: url,
        mainAddress: address,
        description: description,
        numberOfEmployees: numberOfEmployees.value,
        logo: logo
        }""",
        script_data
    )
    data = {}
    for element in selector.xpath("//div[contains(@data-test-id, 'about-us')]"):
        name = element.xpath(".//dt/text()").get().strip()
        value = element.xpath(".//dd/text()").get().strip()
        data[name] = value
    addresses = []
    for element in selector.xpath("//div[contains(@id, 'address') and @id != 'address-0']"):
        address_lines = element.xpath(".//p/text()").getall()
        address = ", ".join(line.replace("\n", "").strip() for line in address_lines)
        addresses.append(address)
    affiliated_pages = []
    for element in selector.xpath("//section[@data-test-id='affiliated-pages']/div/div/ul/li"):
        affiliated_pages.append({
            "name": element.xpath(".//a/div/h3/text()").get().strip(),
            "industry": strip_text(element.xpath(".//a/div/p[1]/text()").get()),
            "address": strip_text(element.xpath(".//a/div/p[2]/text()").get()),
            "linkeinUrl": element.xpath(".//a/@href").get().split("?")[0]
        })
    similar_pages = []
    for element in selector.xpath("//section[@data-test-id='similar-pages']/div/div/ul/li"):
        similar_pages.append({
            "name": element.xpath(".//a/div/h3/text().get().strip()"),
            "industry": strip_text(element.xpath(".//a/div/p[1]/text()").get()),
            "address": strip_text(element.xpath(".//a/div/p[2]/text()").get()),
            "linkeinUrl": element.xpath(".//a/@href").get().split("?")[0]
        })
    data = {**script_data, **data}
    data["addresses"] = addresses    
    data["affiliatedPages"] = affiliated_pages
    data["similarPages"] = similar_pages
    return data

async def scrape_company(urls: List[str]) -> List[Dict]:
    """Scrape public LinkedIn company pages"""
    to_scrape = [client.get(url) for url in urls]
    data = []
    for response in asyncio.as_completed(to_scrape):
        response = await response
        data.append(parse_company(response))
    log.success(f"Scraped {len(data)} companies from LinkedIn")
    return data

async def main(url: str):
    profile_data = await scrape_company([url])
    return profile_data


###### Preprocessing functions ######

# Initialize an async httpx client
client = AsyncClient(
    # Enable http2
    http2=True,
    # Add basic browser-like headers to prevent being blocked
    headers={
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
    },
)

from typing import Dict

def refine_profile(data: Dict) -> Dict: 
    """Refine and clean the parsed profile data"""
    parsed_data = {}
    
    # Extract profile data
    profile_data = [key for key in data["@graph"] if key["@type"]=="Person"][0]
    profile_data["worksFor"] = [profile_data["worksFor"][0]]
    
    # Extract articles/posts data
    articles = [key for key in data["@graph"] if key["@type"]=="Article"]
    for article in articles:
        selector = Selector(article["articleBody"])
        article["articleBody"] = "".join(selector.xpath("//p/text()").getall())
    
    # Extract experience data
    experience = [key for key in data["@graph"] if key["@type"] == "OrganizationRole"]
    
    # Add all extracted data to parsed_data
    parsed_data["profile"] = profile_data
    parsed_data["posts"] = articles
    parsed_data["experience"] = experience
    
    return parsed_data


def parse_profile(response: Response) -> Dict:
    """Parse profile data from hidden script tags"""
    assert response.status_code == 200, "Request is blocked, use the ScrapFly codetabs"
    selector = Selector(response.text)
    data = json.loads(selector.xpath("//script[@type='application/ld+json']/text()").get())
    refined_data = refine_profile(data)
    return refined_data

async def scrape_profile(urls: List[str]) -> List[Dict]:
    """Scrape public LinkedIn profile pages"""
    to_scrape = [client.get(url) for url in urls]
    data = []
    # Scrape the URLs concurrently
    for response in asyncio.as_completed(to_scrape):
        response = await response
        profile_data = parse_profile(response)
        data.append(profile_data)
    log.success(f"Scraped {len(data)} profiles from LinkedIn")
    return data

import jmespath
import asyncio
import json
from typing import List, Dict
from httpx import AsyncClient, Response
from parsel import Selector
from loguru import logger as log

# initialize an async httpx client
client = AsyncClient(
    # enable http2
    http2=True,
    # add basic browser like headers to prevent being blocked
    headers={
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
    },
    follow_redirects=True
)

def strip_text(text):
    """remove extra spaces while handling None values"""
    return text.strip() if text != None else text


def parse_company(response: Response) -> Dict:
    """parse company main overview page"""
    assert response.status_code == 200, "request is blocked, use the ScrapFly codetabs"
    selector = Selector(response.text)
    script_data = json.loads(selector.xpath("//script[@type='application/ld+json']/text()").get())
    script_data = jmespath.search(
        """{
        name: name,
        url: url,
        mainAddress: address,
        description: description,
        numberOfEmployees: numberOfEmployees.value,
        logo: logo
        }""",
        script_data
    )
    data = {}
    for element in selector.xpath("//div[contains(@data-test-id, 'about-us')]"):
        name = element.xpath(".//dt/text()").get().strip()
        value = element.xpath(".//dd/text()").get().strip()
        data[name] = value
    addresses = []
    for element in selector.xpath("//div[contains(@id, 'address') and @id != 'address-0']"):
        address_lines = element.xpath(".//p/text()").getall()
        address = ", ".join(line.replace("\n", "").strip() for line in address_lines)
        addresses.append(address)
    affiliated_pages = []
    for element in selector.xpath("//section[@data-test-id='affiliated-pages']/div/div/ul/li"):
        affiliated_pages.append({
            "name": element.xpath(".//a/div/h3/text()").get().strip(),
            "industry": strip_text(element.xpath(".//a/div/p[1]/text()").get()),
            "address": strip_text(element.xpath(".//a/div/p[2]/text()").get()),
            "linkeinUrl": element.xpath(".//a/@href").get().split("?")[0]
        })
    similar_pages = []
    for element in selector.xpath("//section[@data-test-id='similar-pages']/div/div/ul/li"):
        similar_pages.append({
            "name": element.xpath(".//a/div/h3/text()").get().strip(),
            "industry": strip_text(element.xpath(".//a/div/p[1]/text()").get()),
            "address": strip_text(element.xpath(".//a/div/p[2]/text()").get()),
            "linkeinUrl": element.xpath(".//a/@href").get().split("?")[0]
        })
    data = {**script_data, **data}
    data["addresses"] = addresses    
    data["affiliatedPages"] = affiliated_pages
    data["similarPages"] = similar_pages
    return data


async def scrape_company(urls: List[str]) -> List[Dict]:
    """scrape prublic linkedin company pages"""
    to_scrape = [client.get(url) for url in urls]
    data = []
    for response in asyncio.as_completed(to_scrape):
        response = await response
        data.append(parse_company(response))
    log.success(f"scraped {len(data)} companies from Linkedin")
    return data

def linkedin_analysis():
    
    # Add buttons for different analyses
    analysis_type = st.radio("Select Analysis Type", ["LinkedIn Public Profile Pages", "LinkedIn Company Pages","LinkedIn Job Search Pages"])
    
    # Perform analysis based on the selected analysis type
    if analysis_type == "LinkedIn Public Profile Pages":
        # Add functionality for personal link analysis
        st.header("LinkedIn Public Profile Pages Analysis")
        st.write("LinkedIn Public Profile Pages:")
        st.write("Please enter the URL of the LinkedIn profile you want to analyze:")
        profile_url = st.text_input("LinkedIn Profile URL")
        if st.button("Analyze"):
            if profile_url:
                try:
                    profile_data = asyncio.run(scrape_profile([profile_url]))
                    
                    for item in profile_data:
                        st.write(f"Name: {item['profile']['name']}")
                        st.write(f"Job Title: {', '.join(item['profile']['jobTitle'])}")
                        
                        # Extract and display education details
                        education_details = item['profile'].get('alumniOf', [])
                        if education_details:
                            st.write("Education:")
                            for education in education_details:
                                st.write(f"Name: {education['name']}")
                                st.write(f"Start Date: {education['member']['startDate']}")
                                st.write(f"End Date: {education['member']['endDate']}")
                        
                        st.write(f"Location: {item['profile']['address']['addressLocality'] + ', ' + item['profile']['address']['addressCountry']}")
                        st.write(f"Current Company: {item['profile']['worksFor'][0]['name']}")
                        st.write(f"Followers: {item['profile']['interactionStatistic']['userInteractionCount']}")
                        st.write(f"Description: {item['profile']['description']}")
                        st.write(f"Experience: {item['experience']}")
                    
                except Exception as e:
                    st.error(f"Error occurred: {e}")
            else:
                st.warning("Please enter a LinkedIn profile URL to analyze.")
    # elif analysis_type == "Connections":


    #     uploaded_file = st.file_uploader("Choose a file")
    #     if uploaded_file is not None:


    #         # Can be used wherever a "file-like" object is accepted:
    #         df = pd.read_csv(uploaded_file, skiprows=list(range(2)))
    #     #      df = df.sort_values(by='Company', ascending=True)
            
    #         #  st.dataframe(df.head())
    #         #  st.markdown("## **Use the select feature on the side bar to filter by company**")
    #         options = df['Company'].unique().tolist()
    #         selected_options = st.sidebar.multiselect('Select single or multiple company(s)', options)

    #         filtered_df = df[df["Company"].isin(selected_options)]
            
    #         st.dataframe(filtered_df)

    #         group_filtered_company = filtered_df.groupby(by = 'Company').count().reset_index()
    #         group_filtered_company
    #         group_filtered_company=group_filtered_company.sort_values(by = 'Connected On',ascending=False).reset_index(drop=True)

    #         fig = px.bar(group_filtered_company[:50],
    #                 x = 'Company',
    #                 y = 'Connected On',
    #                 labels = {'Connected On':'Number of Connections'},
    #                 width = 1000,
    #                 height = 500,
    #                 title = 'Companies that my Connections are working at')
    #         st.plotly_chart(fig)

    #         fig_tree = px.treemap(group_filtered_company[:50], path = ['Company', 'Position'],
    #                         values = 'Connected On',
    #                         labels = {'Connected On' : 'Number of Connections'},
    #                         width = 1000,
    #                         height = 600,
    #                         title = 'Tree Map for companies that my connections are working at')
    #         st.plotly_chart(fig_tree)


    #         st.markdown("## **Full Connection Analysis**")
    #         # st.write(df)

    #         group_company = df.groupby(by = 'Company').count().reset_index()
    #         group_company=group_company.sort_values(by = 'Connected On',ascending=False).reset_index(drop=True)

    #         fig = px.bar(group_company[:50],
    #                 x = 'Company',
    #                 y = 'Connected On',
    #                 labels = {'Connected On':'Number of Connections'},
    #                 width = 1000,
    #                 height = 900,
    #                 title = 'Companies that my Connections are working at')
    #         st.plotly_chart(fig)

    #         fig_tree = px.treemap(group_company[:50], path = ['Company', 'Position'],
    #                         values = 'Connected On',
    #                         labels = {'Connected On' : 'Number of Connections'},
    #                         width = 1000,
    #                         height = 900,
    #                         title = 'Tree Map for companies that my connections are working at')
    #         st.plotly_chart(fig_tree)

    #         st.markdown("#### **Number of Positions occupied by my Linkedin Connections**")
    #         # df['Position'].value_counts()/len(df) * 100 > 0.20
    #         linkedin_position = pd.DataFrame(df['Position'].value_counts()[df['Position'].value_counts()/len(df) * 100 > 0.20])
    #         linkedin_position

    #         fig_position = px.bar(df.groupby(by = 'Position').count().sort_values(by = 'First Name', ascending=False)
    #                 [:50].reset_index(),
    #                 x = 'Position',
    #                 y = 'Connected On',
    #                 width = 1000,
    #                 height = 900,
    #                 labels = {'Connected On': 'Number of Connections'},
    #                 title = 'The various Positions occupied by my LinkedIn Connections')
    #         st.plotly_chart(fig_position)
    
    elif analysis_type == "LinkedIn Job Search Pages":
        
        # # Streamlit user interface
        # st.header("LinkedIn Job Search Analysis")
        # st.write("Please enter the keyword and location for the LinkedIn job search:")

        # keyword = st.text_input("Job Keyword", "Python Developer")
        # location = st.text_input("Job Location", "United States")
        # max_pages = st.number_input("Max pages to scrape (each page contains 25 jobs)", min_value=1, max_value=20, value=3, step=1)

        # if st.button("Analyze"):
        #     if keyword and location:
        #         try:
        #             job_search_data = asyncio.run(main_job_search(keyword, location, max_pages))
                    
        #             st.write(f"Total Jobs Found: {len(job_search_data)}")
        #             for job in job_search_data:
        #                 st.write(f"Title: {job['title']}")
        #                 st.write(f"Company: {job['company']}")
        #                 st.write(f"Location: {job['address']}")
        #                 st.write(f"Posted: {job['timeAdded']}")
        #                 st.write(f"Job URL: {job['jobUrl']}")
        #                 st.write(f"Company URL: {job['companyUrl']}")
        #                 st.write(f"Salary: {job['salary']}")
        #                 st.write("---")
                        
        #         except Exception as e:
        #             st.error(f"Error occurred: {e}")
        #     else:
        #         st.warning("Please enter both a keyword and location for the job search.")
        
        # Streamlit user interface
        st.header("LinkedIn Job Search Analysis")
        st.write("Please enter the keyword and location for the LinkedIn job search:")

        keyword = st.text_input("Job Keyword", "Python Developer")
        location = st.text_input("Job Location", "United States")
        max_pages = st.number_input("Max pages to scrape (each page contains 25 jobs)", min_value=1, max_value=20, value=3, step=1)

        if st.button("Analyze"):
            if keyword and location:
                try:
                    job_search_data = asyncio.run(main_job_search(keyword, location, max_pages))
                    df = pd.DataFrame(job_search_data)

                    st.write(f"Total Jobs Found: {len(job_search_data)}")
                    st.dataframe(df)
                    
                except Exception as e:
                    st.error(f"Error occurred: {e}")
            else:
                st.warning("Please enter both a keyword and location for the job search.")
                
    elif analysis_type == "LinkedIn Company Jobs":
        
        # Streamlit user interface
        st.header("LinkedIn Job Search Analysis")
        st.write("Please enter the URL of the LinkedIn job search page you want to analyze:")

        job_search_url = st.text_input("LinkedIn Job Search URL")
        max_pages = st.number_input("Max pages to scrape (each page contains 25 jobs)", min_value=1, max_value=20, value=3, step=1)
        if st.button("Analyze"):
            if job_search_url:
                try:
                    job_search_data = asyncio.run(main_jobs(job_search_url, max_pages))
                    
                    st.write(f"Total Jobs Found: {len(job_search_data)}")
                    for job in job_search_data:
                        st.write(f"Title: {job['title']}")
                        st.write(f"Company: {job['company']}")
                        st.write(f"Location: {job['address']}")
                        st.write(f"Posted: {job['timeAdded']}")
                        st.write(f"Job URL: {job['jobUrl']}")
                        st.write(f"Company URL: {job['companyUrl']}")
                        st.write(f"Salary: {job['salary']}")
                        st.write("---")
                        
                except Exception as e:
                    st.error(f"Error occurred: {e}")
            else:
                st.warning("Please enter a LinkedIn job search URL to analyze.")
    elif analysis_type == "LinkedIn Company Pages":
        # # Add functionality for job analysis
        # st.write("Performing job analysis...")

        # Streamlit user interface
        st.header("LinkedIn Company Pages Analysis")
        st.write("Please enter the URL of the LinkedIn company profile you want to analyze:")

        profile_url = st.text_input("LinkedIn Profile URL")
        if st.button("Analyze"):
            if profile_url:
                try:
                    profile_data = asyncio.run(main(profile_url))
                    
                    for item in profile_data:
                        st.write(f"Name: {item.get('name', 'N/A')}")
                        st.write(f"URL: {item.get('url', 'N/A')}")
                        st.write(f"Main Address: {item.get('mainAddress', 'N/A')}")
                        st.write(f"Description: {item.get('description', 'N/A')}")
                        st.write(f"Number of Employees: {item.get('numberOfEmployees', 'N/A')}")
                        st.write(f"Logo URL: {item.get('logo', 'N/A')}")
                        
                        st.write("Addresses:")
                        for address in item.get('addresses', []):
                            st.write(f"- {address}")
                        
                        st.write("Affiliated Pages:")
                        for affiliated in item.get('affiliatedPages', []):
                            st.write(f"- Name: {affiliated['name']}, Industry: {affiliated['industry']}, Address: {affiliated['address']}, LinkedIn URL: {affiliated['linkeinUrl']}")
                        
                        st.write("Similar Pages:")
                        for similar in item.get('similarPages', []):
                            st.write(f"- Name: {similar['name']}, Industry: {similar['industry']}, Address: {similar['address']}, LinkedIn URL: {similar['linkeinUrl']}")
                        
                except Exception as e:
                    st.error(f"Error occurred: {e}")
            else:
                st.warning("Please enter a LinkedIn company profile URL to analyze.")

# Generates a link allowing the data in a given panda dataframe to be downloaded in csv format 
def get_csv_download_link(df,filename,text):
    csv = df.to_csv(index=False)
    ## bytes conversions
    b64 = base64.b64encode(csv.encode()).decode()      
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href


# Reads Pdf file and check_extractable
def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,
                                      caching=True,
                                      check_extractable=True):
            page_interpreter.process_page(page)
            print(page)
        text = fake_file_handle.getvalue()

    ## close open handles
    converter.close()
    fake_file_handle.close()
    return text


# show uploaded file path to view pdf_display
def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


# course recommendations which has data already loaded from Courses.py
def course_recommender(course_list):
    st.subheader("**Courses & Certificates Recommendations 👨‍🎓**")
    c = 0
    rec_course = []
    ## slider to choose from range 1-10
    no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 10, 5)
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break
    return rec_course


###### Database Stuffs ######


# sql connector
connection = pymysql.connect(host='localhost',user='root',password='varshaa102@#',db='cv')
cursor = connection.cursor()


# inserting miscellaneous data, fetched results, prediction and recommendation into user_data table
def insert_data(sec_token,ip_add,host_name,dev_user,os_name_ver,latlong,city,state,country,act_name,act_mail,act_mob,name,email,res_score,timestamp,no_of_pages,reco_field,cand_level,skills,recommended_skills,courses,pdf_name):
    DB_table_name = 'user_data'
    insert_sql = "insert into " + DB_table_name + """
    values (0,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    rec_values = (str(sec_token),str(ip_add),host_name,dev_user,os_name_ver,str(latlong),city,state,country,act_name,act_mail,act_mob,name,email,str(res_score),timestamp,str(no_of_pages),reco_field,cand_level,skills,recommended_skills,courses,pdf_name)
    cursor.execute(insert_sql, rec_values)
    connection.commit()


# inserting feedback data into user_feedback table
def insertf_data(feed_name,feed_email,feed_score,comments,Timestamp):
    DBf_table_name = 'user_feedback'
    insertfeed_sql = "insert into " + DBf_table_name + """
    values (0,%s,%s,%s,%s,%s)"""
    rec_values = (feed_name, feed_email, feed_score, comments, Timestamp)
    cursor.execute(insertfeed_sql, rec_values)
    connection.commit()


###### Setting Page Configuration (favicon, Logo, Title) ######


st.set_page_config(
   page_title="Talent Acquisition Companion",
   page_icon='./Logo/recommend.png',
)


###### Main function run() ######


def run():
    
    # (Logo, Heading, Sidebar etc)
    img = Image.open('./Logo/RESUM.png')
    st.image(img)
    st.sidebar.markdown("# Choose Something...")
    activities = [ "About","Admin","Resume Analysis", "Linkedin Analysis","Feedback"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)
    # link = '<b>Built with 🤍 by <a href="https://dnoobnerd.netlify.app/" style="text-decoration: none; color: #021659;">Deepak Padhi</a></b>' 
    # st.sidebar.markdown(link, unsafe_allow_html=True)
    st.sidebar.markdown('''
        <!-- site visitors -->

        <div id="sfct2xghr8ak6lfqt3kgru233378jya38dy" hidden></div>

        <noscript>
            <a href="https://www.freecounterstat.com" title="hit counter">
                <img src="https://counter9.stat.ovh/private/freecounterstat.php?c=t2xghr8ak6lfqt3kgru233378jya38dy" border="0" title="hit counter" alt="hit counter"> -->
            </a>
        </noscript>
    
        <p>Visitors <img src="https://counter9.stat.ovh/private/freecounterstat.php?c=t2xghr8ak6lfqt3kgru233378jya38dy" title="Free Counter" Alt="web counter" width="60px"  border="0" /></p>
    
    ''', unsafe_allow_html=True)

    ###### Creating Database and Table ######


    # Create the DB
    db_sql = """CREATE DATABASE IF NOT EXISTS CV;"""
    cursor.execute(db_sql)


    # Create table user_data and user_feedback
    DB_table_name = 'user_data'
    table_sql = "CREATE TABLE IF NOT EXISTS " + DB_table_name + """
                    (ID INT NOT NULL AUTO_INCREMENT,
                    sec_token varchar(20) NOT NULL,
                    ip_add varchar(50) NULL,
                    host_name varchar(50) NULL,
                    dev_user varchar(50) NULL,
                    os_name_ver varchar(50) NULL,
                    latlong varchar(50) NULL,
                    city varchar(50) NULL,
                    state varchar(50) NULL,
                    country varchar(50) NULL,
                    act_name varchar(50) NOT NULL,
                    act_mail varchar(50) NOT NULL,
                    act_mob varchar(20) NOT NULL,
                    Name varchar(500) NOT NULL,
                    Email_ID VARCHAR(500) NOT NULL,
                    resume_score VARCHAR(8) NOT NULL,
                    Timestamp VARCHAR(50) NOT NULL,
                    Page_no VARCHAR(5) NOT NULL,
                    Predicted_Field BLOB NOT NULL,
                    User_level BLOB NOT NULL,
                    Actual_skills BLOB NOT NULL,
                    Recommended_skills BLOB NOT NULL,
                    Recommended_courses BLOB NOT NULL,
                    pdf_name varchar(50) NOT NULL,
                    PRIMARY KEY (ID)
                    );
                """
    cursor.execute(table_sql)


    DBf_table_name = 'user_feedback'
    tablef_sql = "CREATE TABLE IF NOT EXISTS " + DBf_table_name + """
                    (ID INT NOT NULL AUTO_INCREMENT,
                        feed_name varchar(50) NOT NULL,
                        feed_email VARCHAR(50) NOT NULL,
                        feed_score VARCHAR(5) NOT NULL,
                        comments VARCHAR(100) NULL,
                        Timestamp VARCHAR(50) NOT NULL,
                        PRIMARY KEY (ID)
                    );
                """
    cursor.execute(tablef_sql)


    ###### CODE FOR CLIENT SIDE (USER) ######

    if choice == 'Resume Analysis':
        
        # Collecting Miscellaneous Information
        act_name = st.text_input('Name*')
        act_mail = st.text_input('Mail*')
        act_mob  = st.text_input('Mobile Number*')
        sec_token = secrets.token_urlsafe(12)
        host_name = socket.gethostname()
        ip_add = socket.gethostbyname(host_name)
        dev_user = os.getlogin()
        os_name_ver = platform.system() + " " + platform.release()
        g = geocoder.ip('me')
        latlong = g.latlng
        geolocator = Nominatim(user_agent="http")
        location = geolocator.reverse(latlong, language='en')
        address = location.raw['address']
        cityy = address.get('city', '')
        statee = address.get('state', '')
        countryy = address.get('country', '')  
        city = cityy
        state = statee
        country = countryy


        # Upload Resume
        st.markdown('''<h5 style='text-align: left; color: #021659;'> Upload Your Resume, And Get Smart Recommendations</h5>''',unsafe_allow_html=True)
        
        ## file upload in pdf format
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
        if pdf_file is not None:
            with st.spinner('Hang On While We Cook Magic For You...'):
                time.sleep(4)
        
            ### saving the uploaded resume to folder
            save_image_path = './Uploaded_Resumes/'+pdf_file.name
            pdf_name = pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_image_path)

            ### parsing and extracting whole resume 
            resume_data = ResumeParser(save_image_path).get_extracted_data()
            if resume_data:
                
                ## Get the whole resume data into resume_text
                resume_text = pdf_reader(save_image_path)

                ## Showing Analyzed data from (resume_data)
                st.header("**Resume Analysis 🤘**")
                st.success("Hello "+ resume_data['name'])
                st.subheader("**Your Basic info 👀**")
                try:
                    st.text('Name: '+resume_data['name'])
                    st.text('Email: ' + resume_data['email'])
                    st.text('Contact: ' + resume_data['mobile_number'])
                    st.text('Degree: '+str(resume_data['degree']))                    
                    st.text('Resume pages: '+str(resume_data['no_of_pages']))

                except:
                    pass
                ## Predicting Candidate Experience Level 

                ### Trying with different possibilities
                cand_level = ''
                if resume_data['no_of_pages'] < 1:                
                    cand_level = "NA"
                    st.markdown( '''<h4 style='text-align: left; color: #d73b5c;'>You are at Fresher level!</h4>''',unsafe_allow_html=True)
                
                #### if internship then intermediate level
                elif 'INTERNSHIP' in resume_text:
                    cand_level = "Intermediate"
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''',unsafe_allow_html=True)
                elif 'INTERNSHIPS' in resume_text:
                    cand_level = "Intermediate"
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''',unsafe_allow_html=True)
                elif 'Internship' in resume_text:
                    cand_level = "Intermediate"
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''',unsafe_allow_html=True)
                elif 'Internships' in resume_text:
                    cand_level = "Intermediate"
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''',unsafe_allow_html=True)
                
                #### if Work Experience/Experience then Experience level
                elif 'EXPERIENCE' in resume_text:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''',unsafe_allow_html=True)
                elif 'WORK EXPERIENCE' in resume_text:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''',unsafe_allow_html=True)
                elif 'Experience' in resume_text:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''',unsafe_allow_html=True)
                elif 'Work Experience' in resume_text:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''',unsafe_allow_html=True)
                else:
                    cand_level = "Fresher"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at Fresher level!!''',unsafe_allow_html=True)


                ## Skills Analyzing and Recommendation
                st.subheader("**Skills Recommendation 💡**")
                
                ### Current Analyzed Skills
                keywords = st_tags(label='### Your Current Skills',
                text='See our skills recommendation below',value=resume_data['skills'],key = '1  ')

                ### Keywords for Recommendations
                ds_keyword = ['tensorflow','keras','pytorch','machine learning','deep Learning','flask','streamlit']
                web_keyword = ['react', 'django', 'node jS', 'react js', 'php', 'laravel', 'magento', 'wordpress','javascript', 'angular js', 'C#', 'Asp.net', 'flask']
                android_keyword = ['android','android development','flutter','kotlin','xml','kivy']
                ios_keyword = ['ios','ios development','swift','cocoa','cocoa touch','xcode']
                uiux_keyword = ['ux','adobe xd','figma','zeplin','balsamiq','ui','prototyping','wireframes','storyframes','adobe photoshop','photoshop','editing','adobe illustrator','illustrator','adobe after effects','after effects','adobe premier pro','premier pro','adobe indesign','indesign','wireframe','solid','grasp','user research','user experience']
                n_any = ['english','communication','writing', 'microsoft office', 'leadership','customer management', 'social media']
                ### Skill Recommendations Starts                
                recommended_skills = []
                reco_field = ''
                rec_course = ''

                ### condition starts to check skills from keywords and predict field
                for i in resume_data['skills']:
                
                    #### Data science recommendation
                    if i.lower() in ds_keyword:
                        print(i.lower())
                        reco_field = 'Data Science'
                        st.success("** Our analysis says you are looking for Data Science Jobs.**")
                        recommended_skills = ['Data Visualization','Predictive Analysis','Statistical Modeling','Data Mining','Clustering & Classification','Data Analytics','Quantitative Analysis','Web Scraping','ML Algorithms','Keras','Pytorch','Probability','Scikit-learn','Tensorflow',"Flask",'Streamlit']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '2')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job</h5>''',unsafe_allow_html=True)
                        # course recommendation
                        rec_course = course_recommender(ds_course)
                        break

                    #### Web development recommendation
                    elif i.lower() in web_keyword:
                        print(i.lower())
                        reco_field = 'Web Development'
                        st.success("** Our analysis says you are looking for Web Development Jobs **")
                        recommended_skills = ['React','Django','Node JS','React JS','php','laravel','Magento','wordpress','Javascript','Angular JS','c#','Flask','SDK']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '3')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h5>''',unsafe_allow_html=True)
                        # course recommendation
                        rec_course = course_recommender(web_course)
                        break

                    #### Android App Development
                    elif i.lower() in android_keyword:
                        print(i.lower())
                        reco_field = 'Android Development'
                        st.success("** Our analysis says you are looking for Android App Development Jobs **")
                        recommended_skills = ['Android','Android development','Flutter','Kotlin','XML','Java','Kivy','GIT','SDK','SQLite']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '4')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h5>''',unsafe_allow_html=True)
                        # course recommendation
                        rec_course = course_recommender(android_course)
                        break

                    #### IOS App Development
                    elif i.lower() in ios_keyword:
                        print(i.lower())
                        reco_field = 'IOS Development'
                        st.success("** Our analysis says you are looking for IOS App Development Jobs **")
                        recommended_skills = ['IOS','IOS Development','Swift','Cocoa','Cocoa Touch','Xcode','Objective-C','SQLite','Plist','StoreKit',"UI-Kit",'AV Foundation','Auto-Layout']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '5')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h5>''',unsafe_allow_html=True)
                        # course recommendation
                        rec_course = course_recommender(ios_course)
                        break

                    #### Ui-UX Recommendation
                    elif i.lower() in uiux_keyword:
                        print(i.lower())
                        reco_field = 'UI-UX Development'
                        st.success("** Our analysis says you are looking for UI-UX Development Jobs **")
                        recommended_skills = ['UI','User Experience','Adobe XD','Figma','Zeplin','Balsamiq','Prototyping','Wireframes','Storyframes','Adobe Photoshop','Editing','Illustrator','After Effects','Premier Pro','Indesign','Wireframe','Solid','Grasp','User Research']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '6')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h5>''',unsafe_allow_html=True)
                        # course recommendation
                        rec_course = course_recommender(uiux_course)
                        break

                    #### For Not Any Recommendations
                    elif i.lower() in n_any:
                        print(i.lower())
                        reco_field = 'NA'
                        st.warning("** Currently our tool only predicts and recommends for Data Science, Web, Android, IOS and UI/UX Development**")
                        recommended_skills = ['No Recommendations']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Currently No Recommendations',value=recommended_skills,key = '6')
                        st.markdown('''<h5 style='text-align: left; color: #092851;'>Maybe Available in Future Updates</h5>''',unsafe_allow_html=True)
                        # course recommendation
                        rec_course = "Sorry! Not Available for this Field"
                        break


                ## Resume Scorer & Resume Writing Tips
                st.subheader("**Resume Tips & Ideas 🥂**")
                resume_score = 0
                
                ### Predicting Whether these key points are added to the resume
                if 'Objective' or 'Summary' in resume_text:
                    resume_score = resume_score+6
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Objective/Summary</h4>''',unsafe_allow_html=True)                
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add your career objective, it will give your career intension to the Recruiters.</h4>''',unsafe_allow_html=True)

                if 'Education' or 'School' or 'College'  in resume_text:
                    resume_score = resume_score + 12
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Education Details</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add Education. It will give Your Qualification level to the recruiter</h4>''',unsafe_allow_html=True)

                if 'EXPERIENCE' in resume_text:
                    resume_score = resume_score + 16
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Experience</h4>''',unsafe_allow_html=True)
                elif 'Experience' in resume_text:
                    resume_score = resume_score + 16
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Experience</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add Experience. It will help you to stand out from crowd</h4>''',unsafe_allow_html=True)

                if 'INTERNSHIPS'  in resume_text:
                    resume_score = resume_score + 6
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Internships</h4>''',unsafe_allow_html=True)
                elif 'INTERNSHIP'  in resume_text:
                    resume_score = resume_score + 6
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Internships</h4>''',unsafe_allow_html=True)
                elif 'Internships'  in resume_text:
                    resume_score = resume_score + 6
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Internships</h4>''',unsafe_allow_html=True)
                elif 'Internship'  in resume_text:
                    resume_score = resume_score + 6
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Internships</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add Internships. It will help you to stand out from crowd</h4>''',unsafe_allow_html=True)

                if 'SKILLS'  in resume_text:
                    resume_score = resume_score + 7
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Skills</h4>''',unsafe_allow_html=True)
                elif 'SKILL'  in resume_text:
                    resume_score = resume_score + 7
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Skills</h4>''',unsafe_allow_html=True)
                elif 'Skills'  in resume_text:
                    resume_score = resume_score + 7
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Skills</h4>''',unsafe_allow_html=True)
                elif 'Skill'  in resume_text:
                    resume_score = resume_score + 7
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Skills</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add Skills. It will help you a lot</h4>''',unsafe_allow_html=True)

                if 'HOBBIES' in resume_text:
                    resume_score = resume_score + 4
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Hobbies</h4>''',unsafe_allow_html=True)
                elif 'Hobbies' in resume_text:
                    resume_score = resume_score + 4
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Hobbies</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add Hobbies. It will show your personality to the Recruiters and give the assurance that you are fit for this role or not.</h4>''',unsafe_allow_html=True)

                if 'INTERESTS'in resume_text:
                    resume_score = resume_score + 5
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Interest</h4>''',unsafe_allow_html=True)
                elif 'Interests'in resume_text:
                    resume_score = resume_score + 5
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Interest</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add Interest. It will show your interest other that job.</h4>''',unsafe_allow_html=True)

                if 'ACHIEVEMENTS' in resume_text:
                    resume_score = resume_score + 13
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Achievements </h4>''',unsafe_allow_html=True)
                elif 'Achievements' in resume_text:
                    resume_score = resume_score + 13
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Achievements </h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add Achievements. It will show that you are capable for the required position.</h4>''',unsafe_allow_html=True)

                if 'CERTIFICATIONS' in resume_text:
                    resume_score = resume_score + 12
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Certifications </h4>''',unsafe_allow_html=True)
                elif 'Certifications' in resume_text:
                    resume_score = resume_score + 12
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Certifications </h4>''',unsafe_allow_html=True)
                elif 'Certification' in resume_text:
                    resume_score = resume_score + 12
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Certifications </h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add Certifications. It will show that you have done some specialization for the required position.</h4>''',unsafe_allow_html=True)

                if 'PROJECTS' in resume_text:
                    resume_score = resume_score + 19
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects</h4>''',unsafe_allow_html=True)
                elif 'PROJECT' in resume_text:
                    resume_score = resume_score + 19
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects</h4>''',unsafe_allow_html=True)
                elif 'Projects' in resume_text:
                    resume_score = resume_score + 19
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects</h4>''',unsafe_allow_html=True)
                elif 'Project' in resume_text:
                    resume_score = resume_score + 19
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add Projects. It will show that you have done work related the required position or not.</h4>''',unsafe_allow_html=True)

                st.subheader("**Resume Score 📝**")
                
                st.markdown(
                    """
                    <style>
                        .stProgress > div > div > div > div {
                            background-color: #d73b5c;
                        }
                    </style>""",
                    unsafe_allow_html=True,
                )

                ### Score Bar
                my_bar = st.progress(0)
                score = 0
                for percent_complete in range(resume_score):
                    score +=1
                    time.sleep(0.1)
                    my_bar.progress(percent_complete + 1)

                ### Score
                st.success('** Your Resume Writing Score: ' + str(score)+'**')
                st.warning("** Note: This score is calculated based on the content that you have in your Resume. **")

                # print(str(sec_token), str(ip_add), (host_name), (dev_user), (os_name_ver), (latlong), (city), (state), (country), (act_name), (act_mail), (act_mob), resume_data['name'], resume_data['email'], str(resume_score), timestamp, str(resume_data['no_of_pages']), reco_field, cand_level, str(resume_data['skills']), str(recommended_skills), str(rec_course), pdf_name)


                ### Getting Current Date and Time
                ts = time.time()
                cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                timestamp = str(cur_date+'_'+cur_time)


                ## Calling insert_data to add all the data into user_data                
                insert_data(str(sec_token), str(ip_add), (host_name), (dev_user), (os_name_ver), (latlong), (city), (state), (country), (act_name), (act_mail), (act_mob), resume_data['name'], resume_data['email'], str(resume_score), timestamp, str(resume_data['no_of_pages']), reco_field, cand_level, str(resume_data['skills']), str(recommended_skills), str(rec_course), pdf_name)

                ## Recommending Resume Writing Video
                st.header("**Bonus Video for Resume Writing Tips💡**")
                resume_vid = random.choice(resume_videos)
                st.video(resume_vid)

                ## Recommending Interview Preparation Video
                st.header("**Bonus Video for Interview Tips💡**")
                interview_vid = random.choice(interview_videos)
                st.video(interview_vid)

                ## On Successful Result 
                st.balloons()

            else:
                st.error('Something went wrong..')                

    ###### CODE FOR FEEDBACK SIDE ######
    elif choice == 'Feedback':   
        
        # timestamp 
        ts = time.time()
        cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
        cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
        timestamp = str(cur_date+'_'+cur_time)

        # Feedback Form
        with st.form("my_form"):
            st.write("Feedback form")            
            feed_name = st.text_input('Name')
            feed_email = st.text_input('Email')
            feed_score = st.slider('Rate Us From 1 - 5', 1, 5)
            comments = st.text_input('Comments')
            Timestamp = timestamp        
            submitted = st.form_submit_button("Submit")
            if submitted:
                ## Calling insertf_data to add dat into user feedback
                insertf_data(feed_name,feed_email,feed_score,comments,Timestamp)    
                ## Success Message 
                st.success("Thanks! Your Feedback was recorded.") 
                ## On Successful Submit
                st.balloons()    


        # query to fetch data from user feedback table
        query = 'select * from user_feedback'        
        plotfeed_data = pd.read_sql(query, connection)                        


        # fetching feed_score from the query and getting the unique values and total value count 
        labels = plotfeed_data.feed_score.unique()
        values = plotfeed_data.feed_score.value_counts()


        # plotting pie chart for user ratings
        st.subheader("**Past User Rating's**")
        fig = px.pie(values=values, names=labels, title="Chart of User Rating Score From 1 - 5", color_discrete_sequence=px.colors.sequential.Aggrnyl)
        st.plotly_chart(fig)


        #  Fetching Comment History
        cursor.execute('select feed_name, comments from user_feedback')
        plfeed_cmt_data = cursor.fetchall()

        st.subheader("**User Comment's**")
        dff = pd.DataFrame(plfeed_cmt_data, columns=['User', 'Comment'])
        st.dataframe(dff, width=1000)

    
    ###### CODE FOR ABOUT PAGE ######
    elif choice == 'About':   

        st.header("**About The Tool - TALENT ACQUISITION COMPANION**")

        st.markdown('''
        <div style="width: 190%; padding: 0px;">
        <p align='justify'>
            A tool which parses information from a resume using natural language processing and finds the keywords, cluster them onto sectors based on their keywords. And lastly show recommendations, predictions, analytics to the applicant based on keyword matching.
        </p>

        <p align="justify">
            <b>How to use it: -</b> <br/><br/>
            <b>About -</b> <br/>
            Welcome to our Resume Analyzer tool! This is your entry point into an innovative platform designed to enhance your career prospects. Here, you’ll find an overview of what our tool can do and how it can assist you in improving your resume and professional profile. Dive in to learn more about the features and functionalities that make our tool unique.<br/><br/>
            <b>Admin -</b> <br/>
            The Admin page is the heart of our tool’s data management system. Here, authorized users can handle all aspects of data processing and analysis. This page provides access to critical functions such as data entry, updating records, and managing user profiles. It ensures that all data is accurately processed and securely handled to deliver the best possible insights and recommendations.<br/><br/>
            <b>Feedback -</b> <br/>
            Your input is invaluable! On the Feedback page, users can provide suggestions and comments about their experience with our tool. Whether you have ideas for new features, encountered any issues, or simply want to share your thoughts, this is the place to do it. Your feedback helps us continually improve and adapt our tool to better meet your needs.<br/><br/>
            <b>Resume Analysis -</b> <br/>
            Ready to take your resume to the next level? The Resume Analysis page is where you upload your resume in PDF format for a comprehensive review. Using advanced natural language processing, our tool will analyze your resume, extract relevant keywords, and provide you with tailored suggestions and reviews. Discover how to enhance your resume’s effectiveness and increase your chances of landing your dream job.<br/><br/>
            <b>LinkedIn Analysis -</b> <br/>
            Optimize your LinkedIn presence with our LinkedIn Analysis page. This feature allows you to analyze company profiles, public profiles, and job listings. It helps you gain valuable insights into industry trends, potential employers, and networking opportunities. Whether you’re job hunting or looking to improve your LinkedIn profile, this tool provides actionable recommendations to boost your professional visibility.<br/><br/>
            
        </p><br/><br/>
        </div>
    
        ''',unsafe_allow_html=True) 
    elif choice == 'Linkedin Analysis': 
        linkedin_analysis()

    ###### CODE FOR ADMIN SIDE (ADMIN) ######
    else:
        st.success('Welcome to Admin Side')

        #  Admin Login
        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type='password')

        if st.button('Login'):
            
            ## Credentials 
            if ad_user == 'admin' and ad_password == 'admin@resume-analyzer':
                
                ### Fetch miscellaneous data from user_data(table) and convert it into dataframe
                cursor.execute('''SELECT ID, ip_add, resume_score, convert(Predicted_Field using utf8), convert(User_level using utf8), city, state, country from user_data''')
                datanalys = cursor.fetchall()
                plot_data = pd.DataFrame(datanalys, columns=['Idt', 'IP_add', 'resume_score', 'Predicted_Field', 'User_Level', 'City', 'State', 'Country'])
                
                ### Total Users Count with a Welcome Message
                values = plot_data.Idt.count()
                st.success("Welcome Deepak ! Total %d " % values + " User's Have Used Our Tool : )")                
                
                ### Fetch user data from user_data(table) and convert it into dataframe
                cursor.execute('''SELECT ID, sec_token, ip_add, act_name, act_mail, act_mob, convert(Predicted_Field using utf8), Timestamp, Name, Email_ID, resume_score, Page_no, pdf_name, convert(User_level using utf8), convert(Actual_skills using utf8), convert(Recommended_skills using utf8), convert(Recommended_courses using utf8), city, state, country, latlong, os_name_ver, host_name, dev_user from user_data''')
                data = cursor.fetchall()                

                st.header("**User's Data**")
                df = pd.DataFrame(data, columns=['ID', 'Token', 'IP Address', 'Name', 'Mail', 'Mobile Number', 'Predicted Field', 'Timestamp',
                                                 'Predicted Name', 'Predicted Mail', 'Resume Score', 'Total Page',  'File Name',   
                                                 'User Level', 'Actual Skills', 'Recommended Skills', 'Recommended Course',
                                                 'City', 'State', 'Country', 'Lat Long', 'Server OS', 'Server Name', 'Server User',])
                
                ### Viewing the dataframe
                st.dataframe(df)
                
                ### Downloading Report of user_data in csv file
                st.markdown(get_csv_download_link(df,'User_Data.csv','Download Report'), unsafe_allow_html=True)

                ### Fetch feedback data from user_feedback(table) and convert it into dataframe
                cursor.execute('''SELECT * from user_feedback''')
                data = cursor.fetchall()

                st.header("**User's Feedback Data**")
                df = pd.DataFrame(data, columns=['ID', 'Name', 'Email', 'Feedback Score', 'Comments', 'Timestamp'])
                st.dataframe(df)

                ### query to fetch data from user_feedback(table)
                query = 'select * from user_feedback'
                plotfeed_data = pd.read_sql(query, connection)                        

                ### Analyzing All the Data's in pie charts

                # fetching feed_score from the query and getting the unique values and total value count 
                labels = plotfeed_data.feed_score.unique()
                values = plotfeed_data.feed_score.value_counts()
                
                # Pie chart for user ratings
                st.subheader("**User Rating's**")
                fig = px.pie(values=values, names=labels, title="Chart of User Rating Score From 1 - 5 🤗", color_discrete_sequence=px.colors.sequential.Aggrnyl)
                st.plotly_chart(fig)

                # fetching Predicted_Field from the query and getting the unique values and total value count                 
                labels = plot_data.Predicted_Field.unique()
                values = plot_data.Predicted_Field.value_counts()

                # Pie chart for predicted field recommendations
                st.subheader("**Pie-Chart for Predicted Field Recommendation**")
                fig = px.pie(df, values=values, names=labels, title='Predicted Field according to the Skills 👽', color_discrete_sequence=px.colors.sequential.Aggrnyl_r)
                st.plotly_chart(fig)

                # fetching User_Level from the query and getting the unique values and total value count                 
                labels = plot_data.User_Level.unique()
                values = plot_data.User_Level.value_counts()

                # Pie chart for User's👨‍💻 Experienced Level
                st.subheader("**Pie-Chart for User's Experienced Level**")
                fig = px.pie(df, values=values, names=labels, title="Pie-Chart 📈 for User's 👨‍💻 Experienced Level", color_discrete_sequence=px.colors.sequential.RdBu)
                st.plotly_chart(fig)

                # fetching resume_score from the query and getting the unique values and total value count                 
                labels = plot_data.resume_score.unique()                
                values = plot_data.resume_score.value_counts()

                # Pie chart for Resume Score
                st.subheader("**Pie-Chart for Resume Score**")
                fig = px.pie(df, values=values, names=labels, title='From 1 to 100 💯', color_discrete_sequence=px.colors.sequential.Agsunset)
                st.plotly_chart(fig)

                # fetching IP_add from the query and getting the unique values and total value count 
                labels = plot_data.IP_add.unique()
                values = plot_data.IP_add.value_counts()

                # Pie chart for Users
                st.subheader("**Pie-Chart for Users App Used Count**")
                fig = px.pie(df, values=values, names=labels, title='Usage Based On IP Address 👥', color_discrete_sequence=px.colors.sequential.matter_r)
                st.plotly_chart(fig)

                # fetching City from the query and getting the unique values and total value count 
                labels = plot_data.City.unique()
                values = plot_data.City.value_counts()

                # Pie chart for City
                st.subheader("**Pie-Chart for City**")
                fig = px.pie(df, values=values, names=labels, title='Usage Based On City 🌆', color_discrete_sequence=px.colors.sequential.Jet)
                st.plotly_chart(fig)

                # fetching State from the query and getting the unique values and total value count 
                labels = plot_data.State.unique()
                values = plot_data.State.value_counts()

                # Pie chart for State
                st.subheader("**Pie-Chart for State**")
                fig = px.pie(df, values=values, names=labels, title='Usage Based on State 🚉', color_discrete_sequence=px.colors.sequential.PuBu_r)
                st.plotly_chart(fig)

                # fetching Country from the query and getting the unique values and total value count 
                labels = plot_data.Country.unique()
                values = plot_data.Country.value_counts()

                # Pie chart for Country
                st.subheader("**Pie-Chart for Country**")
                fig = px.pie(df, values=values, names=labels, title='Usage Based on Country 🌏', color_discrete_sequence=px.colors.sequential.Purpor_r)
                st.plotly_chart(fig)

            ## For Wrong Credentials
            else:
                st.error("Wrong ID & Password Provided")

# Calling the main (run()) function to make the whole process run
run()
