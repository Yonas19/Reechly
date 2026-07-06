from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import concurrent.futures
import os 
from dotenv import load_dotenv

# Import the scraping functions we just built
# Make sure your scraper file is named exactly 'scrapper.py'
from scrapper import get_business_websites, extract_emails_from_url

app = FastAPI()

# Allow our Next.js frontend (which will run on port 3000) to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
load_dotenv()

SENDER_EMAIL = os.getenv("SENDER_EMAIL")     # Replace with your Gmail
APP_PASSWORD = os.getenv("APP_PASSWORD") # Replace with your App Password


class SearchRequest(BaseModel):
    query: str
    max_results: int = 10

class EmailRequest(BaseModel):
    target_emails: List[str]
    subject: str
    body: str



@app.post("/api/scrape")
@app.post("/api/scrape")
def run_scraper(request: SearchRequest):
    try:
        sites = get_business_websites(request.query, max_results=request.max_results)
        results = []
        
        # DOWNGRADED to 3 workers so Render's free tier CPU doesn't crash and timeout
        print(f"Spinning up 3 workers to scan {len(sites)} sites...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_url = {executor.submit(extract_emails_from_url, site): site for site in sites}
            
            for future in concurrent.futures.as_completed(future_to_url):
                site = future_to_url[future]
                try:
                    emails = future.result()
                    # We will now return the site even if 0 emails are found so your UI shows the progress
                    if emails:
                        results.append({"website": site, "emails": emails})
                    else:
                        results.append({"website": site, "emails": ["No emails found on site"]})
                except Exception as e:
                    print(f"Worker crashed on {site}: {e}")
                
        return {"status": "success", "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/api/send")
def send_emails(request: EmailRequest):
    if not request.target_emails:
        raise HTTPException(status_code=400, detail="No emails provided.")
        
    sent_count = 0
    failed_emails = []

    try:
        # Connect to Gmail once
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        
        # Loop through the targets and send individually
        for email in request.target_emails:
            try:
                msg = MIMEMultipart()
                msg['From'] = SENDER_EMAIL
                msg['To'] = email
                msg['Subject'] = request.subject
                msg.attach(MIMEText(request.body, 'plain'))
                
                server.send_message(msg)
                sent_count += 1
                
                # Sleep for 2 seconds between emails so Google doesn't flag us as a spam bot
                time.sleep(2) 
            except Exception as e:
                failed_emails.append(email)
                
        server.quit()
        return {
            "status": "success", 
            "message": f"Successfully sent {sent_count} emails.",
            "failed": failed_emails
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to email server: {str(e)}")