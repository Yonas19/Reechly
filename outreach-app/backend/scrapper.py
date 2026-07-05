import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import re
import requests
from urllib.parse import urlparse
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

def get_business_websites(query, max_results=10):
    # 1. CRASH PROOFING: Initialize driver as None
    driver = None
    print("Initializing browser options...")
    
    try:
        # 2. CORRECT SEQUENCE: Create options object FIRST
        options = uc.ChromeOptions()
        
        # 3. Add arguments to the created object
        options.add_argument('--headless')                   
        options.add_argument('--no-sandbox')                
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')

        # Block images to save bandwidth and memory
        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)
        
        print("Launching Stealth Browser in Docker...")
        # REMOVED version_main so undetected-chromedriver matches Docker's Chrome version automatically
        driver = uc.Chrome(options=options)
        
        print(f"Searching Google for: {query}...")
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        driver.get(search_url)

        # 4. Wait for search results container
        try:
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div#search"))
            )
            print("Search results detected! Extracting links...")
        except Exception as e:
            print("Timed out waiting for search results (Google might have shown a CAPTCHA).")
            return []
            
        print("Scrolling to load more results...")
        for _ in range(5): # Reduced from 15 to 5 to avoid timeouts on free cloud tiers
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        # 5. Extract website links
        websites = set()
        seen_domains = set() 
        
        links = driver.find_elements(By.XPATH, "//a[@href]")
        
        for link in links:
            url = link.get_attribute("href")
            if url and "http" in url:
                if any(bad in url.lower() for bad in ['google.', 'facebook.', 'instagram.', 'linkedin.', 'yelp.', 'practo.', 'yellowpages.', 'tripadvisor.']):
                    continue
                    
                clean_url = url.split("?")[0]
                domain = urlparse(clean_url).netloc.replace('www.', '')
                
                if domain and domain not in seen_domains:
                    seen_domains.add(domain)
                    websites.add(clean_url)
                    
                    if len(websites) >= max_results:
                        break
                        
        return list(websites)

    except Exception as e:
        print(f"An error occurred in get_business_websites: {e}")
        return []
        
    finally:
        # 6. SAFE CLEANUP: Only quit if the browser instance actually exists
        if driver is not None:
            try:
                driver.quit()
                print("Browser closed successfully.")
            except:
                pass

def extract_emails_from_url(base_url):
    print(f"Hunting for emails on {base_url} and its contact pages...")
    emails = set()
    
    try:
        site_domain = urlparse(base_url).netloc.replace('www.', '')
    except:
        site_domain = ""

    email_pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0'
    }

    urls_to_check = [base_url]

    # PHASE 1: Find the Contact Page
    try:
        response = requests.get(base_url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        contact_found = False
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            if 'contact' in href or 'about' in href:
                contact_url = urljoin(base_url, link['href'])
                urls_to_check.append(contact_url)
                contact_found = True
                break 
                
        if not contact_found:
            urls_to_check.append(urljoin(base_url, '/contact'))
            urls_to_check.append(urljoin(base_url, '/contact-us'))
            
    except Exception as e:
        pass 

    # PHASE 2: Scan all identified pages for emails
    bad_prefixes = ['privacy', 'abuse', 'press', 'media', 'webmaster', 'hostmaster', 
                    'noreply', 'no-reply', 'careers', 'jobs', 'news', 'sentry', 'admin']

    for target_url in set(urls_to_check):
        try:
            resp = requests.get(target_url, headers=headers, timeout=5)
            found_emails = re.findall(email_pattern, resp.text)
            
            for email in found_emails:
                email_lower = email.lower()
                
                try:
                    local_part, email_domain = email_lower.split('@')
                except ValueError:
                    continue

                if any(ext in email_lower for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.js', '.css']):
                    continue
                    
                if any(bad in local_part for bad in bad_prefixes):
                    continue
                    
                if email_domain == site_domain or email_domain in ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com']:
                    emails.add(email_lower)
                    
        except Exception as e:
            continue

    return list(emails)

if __name__ == "__main__":
    test_query = "dental clinics in Miami"
    print(f"Starting pipeline for: {test_query}\n")
    
    found_sites = get_business_websites(test_query, max_results=5) 
    
    results = []
    for site in found_sites:
        emails = extract_emails_from_url(site)
        results.append({
            "website": site,
            "emails": emails
        })
    
    print("\n--- FINAL RESULTS ---")
    for result in results:
        print(f"Website: {result['website']}")
        print(f"Emails Found: {result['emails']}\n")