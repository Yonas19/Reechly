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
        # 2. Create options object
        options = uc.ChromeOptions()
        
        # 3. Add arguments for Docker container environment compatibility
        options.add_argument('--headless')                   
        options.add_argument('--no-sandbox')                
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')

        # Block images to save bandwidth and memory
        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)
        
        print("Launching Stealth Browser in Docker...")
        driver = uc.Chrome(options=options)
        
        # --- BING SEARCH LOGIC TO BYPASS DATACENTER CAPTCHAs ---
        print(f"Searching Bing for: {query}...")
        search_url = f"https://www.bing.com/search?q={query.replace(' ', '+')}"
        driver.get(search_url)

        # 4. Wait for Bing's main search results container (ID is 'b_results')
        try:
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.ID, "b_results"))
            )
            print("Search results detected! Extracting links...")
        except Exception as e:
            print("Timed out waiting for search results. Bing might have blocked the IP or layout changed.")
            return []
            
        print("Scrolling to load more results...")
        for _ in range(5): 
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        # 5. Extract website links
        websites = set()
        seen_domains = set() 
        
        # Bing organic results are structured within 'li.b_algo h2 a' elements
        links = driver.find_elements(By.CSS_SELECTOR, "li.b_algo h2 a")
        
        # Fallback to grab structural links if selectors shift layout
        if not links:
            links = driver.find_elements(By.XPATH, "//a[@href]")
        
        for link in links:
            try:
                url = link.get_attribute("href")
                if url and "http" in url:
                    # Ignore search engines, social platforms, and major directories
                    if any(bad in url.lower() for bad in [
                        'google.', 'bing.', 'microsoft.', 'facebook.', 'instagram.', 
                        'linkedin.', 'yelp.', 'practo.', 'yellowpages.', 'tripadvisor.'
                    ]):
                        continue
                        
                    clean_url = url.split("?")[0]
                    domain = urlparse(clean_url).netloc.replace('www.', '')
                    
                    if domain and domain not in seen_domains:
                        seen_domains.add(domain)
                        websites.add(clean_url)
                        
                        if len(websites) >= max_results:
                            break
            except Exception:
                continue
                        
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
    print(f"Hunting for emails on {base_url}...")
    emails = set()
    
    try:
        site_domain = urlparse(base_url).netloc.replace('www.', '')
    except:
        site_domain = ""

    email_pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    
    # Updated headers to mimic a modern desktop browser accurately
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    }

    urls_to_check = [base_url]

    # PHASE 1: Find the Contact Page
    try:
        response = requests.get(base_url, headers=headers, timeout=7)
        print(f"-> Homepage status for {base_url}: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        contact_found = False
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            if 'contact' in href or 'about' in href:
                contact_url = urljoin(base_url, link['href'])
                urls_to_check.append(contact_url)
                contact_found = True
                
        if not contact_found:
            urls_to_check.append(urljoin(base_url, '/contact'))
            urls_to_check.append(urljoin(base_url, '/contact-us'))
            
    except Exception as e:
        print(f"-> Could not connect to homepage {base_url}: {e}")

    # PHASE 2: Scan pages for emails
    bad_prefixes = ['privacy', 'abuse', 'press', 'media', 'webmaster', 'hostmaster', 
                    'noreply', 'no-reply', 'careers', 'jobs', 'news', 'sentry', 'admin']

    for target_url in set(urls_to_check):
        try:
            resp = requests.get(target_url, headers=headers, timeout=7)
            if resp.status_code != 200:
                print(f"   Skipping page {target_url} (Status: {resp.status_code})")
                continue
                
            found_emails = re.findall(email_pattern, resp.text)
            
            if found_emails:
                print(f"   Raw text regex matches on {target_url}: {found_emails}")
            
            for email in found_emails:
                email_lower = email.lower()
                
                try:
                    local_part, email_domain = email_lower.split('@')
                except ValueError:
                    continue

                # 1. Clean out code extensions captured by loose regex
                if any(ext in email_lower for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.js', '.css', '.svg']):
                    continue
                    
                # 2. Filter system prefixes
                if any(bad in local_part for bad in bad_prefixes):
                    continue
                    
                # 3. Verified functional format inclusion
                emails.add(email_lower)
                    
        except Exception as e:
            continue

    print(f"-> Total verified emails kept for {base_url}: {list(emails)}")
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