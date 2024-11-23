import re
import cloudscraper
import time
import random
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#########################################################################
#########################################################################
#########################################################################
#########################################################################

def get_company_details(company, link):
    scraper = cloudscraper.create_scraper()
    
    try:
        page = scraper.get(link)
        location = BeautifulSoup(page.content, 'html.parser')

        company['id'] = re.search(r"(\d+)(?!.*\d)", link).group()

        try:
            company['address_details'] = location.select_one("div.flex-column.main-details > div.company-address > span").text
        except:
            company['address_details'] = ""
        
        try:
            loc = location.select_one("p > span.distance")
            company['lat'] = loc["data-lat"]
            company['long'] = loc["data-lng"]
        except:
            company['lat'] = ""
            company['long'] = ""
        
        try:                                    
            company['rate'] = location.select_one("div.rating-div-details > p.rating-value").text
        except:
            company['rate'] = ""
        
        try:
            reviews = location.select_one("div.rating-div-details > p.rating-total").text
            company['reviews'] = int(re.search(r"\d+", reviews).group())
        except:
            company['reviews'] = ""
        
        try:
            social_media = location.select("#first-row > div.main-btns-div.company-details > div.social-links-div > a")
            social_accounts = social_media[0]["href"]
            for c in social_media[1:]:
                company['social_accounts'] = social_accounts + " - " + c["href"]
        except:
            company['social_accounts'] = ""
        
        try:
            keys = location.select("div.header-div.header-div-keywords > div > a")
            key_words = keys[0].text
            for k in keys[1:]:
                key_words = key_words + " - " + k.text  

            company['key_words'] = key_words
        except:
            company['key_words'] = ""
        
        try:
            branches = location.select("#branches > a")
            total_branches = re.search(r"(\d+)(?!.*\d)", branches[0]["href"]).group()
            for b in branches[1:]:
                company['total_branches'] = total_branches + " - " + re.search(r"(\d+)(?!.*\d)", b["href"]).group()
        except:
            company['total_branches'] = ""
        
        try:
            all_phones = scraper.get("https://yellowpages.com.eg/en/getPhones/{loc_id}/false".format(loc_id=company['id'])).json()
            company['phone'] = all_phones[0]
        except:
            company['phone'] = ""
        
        try:
            whatsapp = location.select_one("div.action-btns-div.company-details > div.whatsapp-div > a")["href"]
            company['whatsapp'] = re.search(r"\+\d+", whatsapp).group()
        except:
            company['whatsapp'] = ""
    
        logger.info(f"Details for company {company['name']} retrieved successfully.")
    except Exception as e:
        logger.error(f"Error while fetching details for company {company.get('name', 'Unknown')}: {e}")
    
    return company

#########################################################################
#########################################################################
#########################################################################
#########################################################################

def create_scraper_with_headers():
    ua = UserAgent()
    headers = {
        "User-Agent": ua.random,
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }
    scraper = cloudscraper.create_scraper()
    scraper.headers.update(headers)
    logger.info("Created scraper with custom headers.")
    return scraper

#########################################################################
#########################################################################
#########################################################################
#########################################################################

def robust_request(scraper, url, max_retries=4):
    for attempt in range(max_retries):
        try:
            response = scraper.get(url)

            if response.status_code == 200:
                logger.info(f"Request to {url} successful.")
                return response
            else:
                wait_time = random.uniform(1, 3) * (attempt + 1)
                logger.warning(f"Rate limit hit. Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed for {url}: {e}")
            scraper = create_scraper_with_headers()
        time.sleep(random.uniform(1, 3))  # General delay between retries
    
    logger.error("Max retries exceeded.")
    return None

#########################################################################
#########################################################################
#########################################################################
#########################################################################

def get_page_links(page_source):
    soup = BeautifulSoup(page_source, 'html.parser')
    company_data = []

    try:
        companyCards_div = soup.find(class_='companyCards')

        if companyCards_div:
            for company_result in companyCards_div.find_all(class_='item-row'):
                # Skip ad sections
                if 'search-ads' in company_result.get('class', []):  
                    continue

                company = {}

                more_info_link = company_result.find(class_='more-info')
                if more_info_link:
                    company['link'] = "https:"+more_info_link.get('href')

                # Extract company name
                name_element = company_result.find(class_='item-title')
                company['name'] = name_element.text.strip() if name_element else ""

                # Extract company description
                description_element = company_result.find(class_='item-aboutUs')
                company['description'] = (
                    description_element.a.text.strip() if description_element and description_element.a else ""
                )

                # Extract location/address
                address_element = company_result.find(class_='address-text')
                company['address'] = address_element.text.strip() if address_element else ""

                # Extract website
                website_element = company_result.find(class_='website')
                company['website'] = (
                    website_element['href'].strip() if website_element and 'href' in website_element.attrs else ""
                )

                # Extract categories
                categories_elements = company_result.find_all(class_='category')
                company['categories'] = [
                    cat.a.text.strip() for cat in categories_elements if cat.a
                ] or [""]

                # Extract image URL
                img_tag = company_result.find('img', class_='openDynamicSlider')
                company['image_url'] = (
                    'https:'+ img_tag['data-src'] if img_tag and 'data-src' in img_tag.attrs else ""
                )

                company_data.append(company)

        # Check if there's a next page button
        next_page_url = None
        pagination = soup.find(class_='pagination')
        if pagination:
            next_page_link = pagination.find('a', {'aria-label': 'Next'})
            if next_page_link and 'href' in next_page_link.attrs:
                next_page_url = "https://yellowpages.com.eg" + next_page_link['href']

        logger.info(f"Extracted {len(company_data)} companies from the page.")
    except Exception as e:
        logger.error(f"Error while extracting company links: {e}")
    
    return company_data, next_page_url

#########################################################################
#########################################################################
#########################################################################
#########################################################################

def get_company_links(keyword, max_results):
    scraper = create_scraper_with_headers()
    company_data = []

    page_url = f"https://yellowpages.com.eg/en/search/{keyword}"

    while len(company_data) < max_results and page_url:
        response = robust_request(scraper, page_url)
        if response:
            page_data, page_url = get_page_links(response.content)
            company_data += page_data
        else:
            break

    logger.info(f"Total companies extracted: {len(company_data)}")
    return company_data[:max_results]

#########################################################################
#########################################################################
#########################################################################
#########################################################################

def scrape_yellowpages(keyword, max_results):
    logger.info(f"Scraping yellowpages for keyword: {keyword} with a limit of {max_results} results.")
    company_dict = get_company_links(keyword, max_results)

    result = []
    for data in company_dict:
        get_company_details(data, data['link'])
        result.append(data)

    logger.info(f"Scraping completed for {len(result)} companies.")
    return result
