import time
import re
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import urllib3
from duckduckgo_search import DDGS

# Disable SSL warning noise in logs due to verify=False overrides
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_business_websites(query, max_results=10):
    """
    Uses DuckDuckGo Search to find websites, avoiding the need for a browser like Selenium.
    This is much more lightweight and suitable for server environments like Render.
    """
    print(f"Searching DuckDuckGo for: {query}...")
    websites = set()
    seen_domains = set()

    try:
        # Use DDGS context manager for clean handling. Fetch more results to have enough to filter.
        with DDGS() as ddgs:
            # ddgs.text returns a generator of results
            search_results = ddgs.text(query, max_results=max_results * 4)
            if not search_results:
                print("No results from search engine.")
                return []

            for r in search_results:
                url = r.get('href')
                if not url:
                    continue

                # Ignore search engines, social platforms, and major directories
                if any(bad in url.lower() for bad in [
                    'google.', 'bing.', 'duckduckgo.', 'facebook.', 'instagram.',
                    'linkedin.', 'yelp.', 'practo.', 'yellowpages.', 'tripadvisor.',
                    'youtube.com', 'wikipedia.org', 'microsoft.'
                ]):
                    continue

                try:
                    clean_url = url.split("?")[0]
                    domain = urlparse(clean_url).netloc.replace('www.', '')

                    if domain and domain not in seen_domains:
                        seen_domains.add(domain)
                        websites.add(clean_url)

                        if len(websites) >= max_results:
                            break
                except Exception:
                    continue

        print(f"Found {len(websites)} unique websites from search.")
        return list(websites)

    except Exception as e:
        print(f"An error occurred in get_business_websites: {e}")
        return []

def decode_cloudflare_email(encoded_string):
    """Decrypts Cloudflare obfuscated emails into plain text."""
    try:
        r = int(encoded_string[:2], 16)
        email = ''.join([chr(int(encoded_string[i:i+2], 16) ^ r) for i in range(2, len(encoded_string), 2)])
        return email
    except Exception:
        return None

def extract_emails_from_url(base_url):
    print(f"\n--- Scanning Site: {base_url} ---")
    emails = set()
    
    try:
        site_domain = urlparse(base_url).netloc.replace('www.', '')
    except:
        site_domain = ""

    email_pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    }

    # Verify or add scheme if missing
    if not base_url.startswith('http'):
        base_url = 'https://' + base_url

    urls_to_check = [base_url]

    # PHASE 1: Find the Contact/About Page links
    try:
        # verify=False bypasses faulty/expired strict SSL certificate handshakes
        response = requests.get(base_url, headers=headers, timeout=12, verify=False)
        print(f"-> Homepage Connection Status: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        contact_found = False
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            if any(kwd in href for kwd in ['contact', 'about', 'info', 'reach', 'team']):
                contact_url = urljoin(base_url, link['href'])
                # Only check internal links to save time and block tracker jumps
                if urlparse(contact_url).netloc.replace('www.', '') == site_domain:
                    urls_to_check.append(contact_url)
                    contact_found = True
                
        if not contact_found:
            urls_to_check.append(urljoin(base_url, '/contact'))
            urls_to_check.append(urljoin(base_url, '/contact-us'))
            urls_to_check.append(urljoin(base_url, '/about'))
            
    except Exception as e:
        print(f"-> Setup Error: Could not connect to homepage base URL: {e}")

    # Remove duplicate URLs to ensure clean scanning loops
    urls_to_check = list(set(urls_to_check))
    print(f"-> Targeted pages to scan for emails: {urls_to_check}")

    # PHASE 2: Scan pages for emails
    bad_prefixes = ['privacy', 'abuse', 'press', 'media', 'webmaster', 'hostmaster', 
                    'noreply', 'no-reply', 'careers', 'jobs', 'news', 'sentry', 'admin']

    for target_url in urls_to_check:
        try:
            print(f"   Scraping target page: {target_url}...")
            resp = requests.get(target_url, headers=headers, timeout=12, verify=False)
            
            if resp.status_code != 200:
                print(f"   ⚠️ Skipped page (Status Code: {resp.status_code})")
                continue
            
            # DELAY INJECTION: Yield a short settlement buffer for chunks to stabilize
            time.sleep(1.5)
                
            # A. Check for Cloudflare Obfuscated Emails
            soup = BeautifulSoup(resp.text, 'html.parser')
            cf_emails = soup.find_all(class_='__cf_email__')
            for cf in cf_emails:
                data_value = cf.get('data-cfemail')
                if data_value:
                    decoded = decode_cloudflare_email(data_value)
                    if decoded:
                        print(f"   [Cloudflare Bypass] Found Decrypted Email: {decoded}")
                        emails.add(decoded.lower())
            
            # B. Standard fallback regular expression match
            found_emails = re.findall(email_pattern, resp.text)
            if found_emails:
                print(f"   Found Regular Regex Email Matches: {found_emails}")
            
            for email in found_emails:
                email_lower = email.lower()
                
                try:
                    local_part, email_domain = email_lower.split('@')
                except ValueError:
                    continue

                # Filter out asset files matched accidentally by open regexes
                if any(ext in email_lower for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.js', '.css', '.svg', '.ico']):
                    continue
                    
                if any(bad in local_part for bad in bad_prefixes):
                    continue
                    
                emails.add(email_lower)
                    
        except Exception as page_error:
            print(f"   ❌ Network/Parsing error on page {target_url}: {page_error}")
            continue

    print(f"-> Final verified list for {base_url}: {list(emails)}")
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