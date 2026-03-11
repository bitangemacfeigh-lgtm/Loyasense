import os
import pandas as pd
import subprocess  # Added for auto-triggering predict.py
from flask import Flask

# Robust Mistral Import for v1.x and v2.x compatibility
try:
    from mistralai import Mistral
except ImportError:
    # Fallback for specific environment pathing issues
    from mistralai.client import MistralClient as Mistral

app = Flask(__name__)

# --- CONFIGURATION ---
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "QiJh8V2kZ3IQL1eYCAnKqJSOJxSHbTyC")

# Initialize client outside the route for performance
try:
    client = Mistral(api_key=MISTRAL_API_KEY)
except Exception as e:
    print(f"Initialization Error: {e}")
    client = None

def get_ai_recommendation(member_id, prob, score):
    """Calls Mistral API to generate a personalized retention pitch."""
    if not client:
        return f"Hello Member {member_id}, we have a special Loyalty Loan offer for you. Contact us today!"

    prompt = f"""
    Act as a SACCO Retention Genius. 
    Member ID: {member_id}
    Churn Risk: {prob:.1f}%
    Engagement Score: {score:.2f}
    
    Task: Write a 1-sentence personalized SMS offer. 
    - If Risk > 50%: Offer a 'Priority Loyalty Loan' with 3% interest discount.
    - If Risk < 50%: Offer a 'Standard Loyalty Loan' with 1.5% discount.
    Tone: Professional, urgent, and empathetic. Start the SMS directly.
    """
    try:
        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Mistral API Error: {e}")
        return f"Hello! As a valued member {member_id}, call us for a special Loyalty Loan offer today!"

def run_analysis():
    """Ensures data exists before showing the report."""
    file_path = 'data/top_50_loyalty_list.csv'
    
    # NEW GENIUS LOGIC: If data is missing, run predict.py automatically
    if not os.path.exists(file_path):
        print("Data missing. Triggering predict.py...")
        try:
            # This triggers your full pipeline to create the CSV
            subprocess.run(["python", "predict.py"], check=True)
        except Exception as e:
            return f"Error auto-generating data: {e}. Please ensure predict.py is in the root folder."

    try:
        df = pd.read_csv(file_path)
        # Analysis threshold: Process anyone with > 5% risk
        high_risk = df[df['churn_probability'] > 0.05].copy()
        
        if high_risk.empty:
            return "Great news! No members currently meet the high-risk churn threshold."

        results = []
        for _, row in high_risk.iterrows():
            member = int(row['member_id'])
            prob = row['churn_probability'] * 100
            score = row['engagement_score']
            
            ai_sms = get_ai_recommendation(member, prob, score)
            results.append(f"Member {member} ({prob:.1f}% risk): {ai_sms}")
        
        return "\n".join(results)
    except Exception as e:
        return f"Analysis Error: {e}"

# --- WEB ROUTES ---

@app.route('/')
def index():
    """Runs the analysis and displays it on the web page."""
    report = run_analysis()
    return f"""
    <html>
        <head>
            <title>LoyaSense AI Dashboard</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 40px; line-height: 1.6; background-color: #f9f9f9; color: #333;">
            <div style="max-width: 800px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h1 style="color: #2c3e50; margin-top: 0;">🤖 LoyaSense Engine</h1>
                <p style="font-size: 1.1em; color: #555;">Agentic Retention Plan | Powered by Mistral AI</p>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                
                <h3 style="color: #2c3e50;">Live Retention Recommendations:</h3>
                <pre style="background: #2d3436; color: #dfe6e9; padding: 20px; border-radius: 8px; white-space: pre-wrap; font-family: 'Courier New', Courier, monospace; font-size: 0.9em;">{report}</pre>
                
                <div style="margin-top: 30px; padding: 15px; border-left: 5px solid #3498db; background: #ebf5fb;">
                    <p style="margin: 0; font-size: 0.9em;"><strong>Status:</strong> Ready for Employer Review</p>
                    <p style="margin: 5px 0 0 0; font-size: 0.8em; color: #7f8c8d;">Region: Virginia (US-East) | Runtime: Python 3.x</p>
                </div>
            </div>
        </body>
    </html>
    """

if __name__ == "__main__":
    # Render assigns a dynamic PORT via environment variables
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)