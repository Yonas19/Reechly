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
    print("Launching Stealth Browser...")
    
    # 1. Use the undetected version of Chrome
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options, version_main=149)
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    
    
    print(f"Searching Google for: {query}...")
    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    driver.get(search_url)

    
    
    # 2. THE FIX: The script will pause here.
    print("\n" + "="*40)
    print("🚦 CHECK THE BROWSER!")
    print("If there is a CAPTCHA, solve it now.")
    print("="*40 + "\n")

    try:
        # Tell Selenium to watch the page for up to 60 seconds.
        # It is looking for the "div#search" element, which is the container Google uses for search results.
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div#search"))
        )
        print("Search results detected! Extracting links...")
    except Exception as e:
        print("Timed out waiting for search results (or CAPTCHA took longer than 60 seconds).")
        driver.quit()
        return []
        

    print("Scrolling to load more results...")
    for _ in range(15): # Scrolls down 5 times
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
    
    # 3. Extract website links (NEW FILTERING LOGIC)
    websites = set()
    seen_domains = set() # This remembers domains so we don't scan the same site twice
    
    links = driver.find_elements(By.XPATH, "//a[@href]")
    
    for link in links:
        url = link.get_attribute("href")
        if url and "http" in url:
            
            # Stricter filter to catch regional variants like .ae or .co.uk
            if any(bad in url.lower() for bad in ['google.', 'facebook.', 'instagram.', 'linkedin.', 'yelp.', 'practo.', 'yellowpages.', 'tripadvisor.']):
                continue
                
            clean_url = url.split("?")[0]
            
            # Extract just the core domain name (e.g., 'dentzzdental.com')
            domain = urlparse(clean_url).netloc.replace('www.', '')
            
            if domain and domain not in seen_domains:
                seen_domains.add(domain)
                websites.add(clean_url)
                
                if len(websites) >= max_results:
                    break
                    
    driver.quit()
    return list(websites)

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

    # Start our checklist with the homepage
    urls_to_check = [base_url]

    # --- PHASE 1: Find the Contact Page ---
    try:
        response = requests.get(base_url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for any link on the homepage that mentions 'contact' or 'about'
        contact_found = False
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            if 'contact' in href or 'about' in href:
                # urljoin securely combines "domain.com" + "/contact"
                contact_url = urljoin(base_url, link['href'])
                urls_to_check.append(contact_url)
                contact_found = True
                break # We just need the first good contact link we find
                
        # If we couldn't find a button, we guess the most common URLs
        if not contact_found:
            urls_to_check.append(urljoin(base_url, '/contact'))
            urls_to_check.append(urljoin(base_url, '/contact-us'))
            
    except Exception as e:
        pass # If the homepage fails to load, we just silently move on

    # --- PHASE 2: Scan all identified pages for emails ---
    bad_prefixes = ['privacy', 'abuse', 'press', 'media', 'webmaster', 'hostmaster', 
                    'noreply', 'no-reply', 'careers', 'jobs', 'news', 'sentry', 'admin']

    # We use set() to remove duplicate URLs so we don't scan the same page twice
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

                # 1. Filter out fake emails (images, system files)
                if any(ext in email_lower for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.js', '.css']):
                    continue
                    
                # 2. Filter out junk prefixes
                if any(bad in local_part for bad in bad_prefixes):
                    continue
                    
                # 3. Keep domain matches or common freemails
                if email_domain == site_domain or email_domain in ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com']:
                    emails.add(email_lower)
                    
        except Exception as e:
            continue

    return list(emails)
if __name__ == "__main__":
    test_query = "dental clinics in Miami"
    print(f"Starting pipeline for: {test_query}\n")
    
    # 1. Get the websites using Selenium
    found_sites = get_business_websites(test_query, max_results=60) 
    
    # 2. Scan each website for emails
    results = []
    for site in found_sites:
        emails = extract_emails_from_url(site)
        results.append({
            "website": site,
            "emails": emails
        })
    
    # 3. Print the final results!
    print("\n--- FINAL RESULTS ---")
    for result in results:
        print(f"Website: {result['website']}")
        print(f"Emails Found: {result['emails']}\n")