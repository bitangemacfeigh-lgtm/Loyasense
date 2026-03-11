import os
import pandas as pd
from flask import Flask

# Robust Mistral Import for v1.x and v2.x compatibility
try:
    from mistralai import Mistral
except ImportError:
    # Fallback for specific environment pathing issues
    from mistralai.client import MistralClient as Mistral

app = Flask(__name__)

# --- CONFIGURATION ---
# We prioritize the Environment Variable for security on Render
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
        # Standard v1/v2 chat completion syntax
        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Mistral API Error: {e}")
        return f"Hello! As a valued member {member_id}, call us for a special Loyalty Loan offer today!"

def run_analysis():
    """The core logic that processes the member list."""
    try:
        # Check if the data folder and file exist
        file_path = 'data/top_50_loyalty_list.csv'
        if not os.path.exists(file_path):
            return "Analysis Pending: Waiting for 'predict.py' to generate at-risk member data."

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
        <head><title>LoyaSense AI</title></head>
        <body style="font-family: sans-serif; padding: 20px; line-height: 1.6;">
            <h1 style="color: #2c3e50;">🤖 LoyaSense Engine: Agentic Action Plan</h1>
            <p>Processing SACCO Behavioral Velocity via Mistral AI...</p>
            <hr>
            <pre style="background: #f4f4f4; padding: 15px; border-radius: 5px; white-space: pre-wrap;">{report}</pre>
            <br>
            <p style="color: #7f8c8d;"><i>Status: Live | Deploy Region: Virginia (US-East)</i></p>
        </body>
    </html>
    """

if __name__ == "__main__":
    # Render assigns a dynamic PORT via environment variables
    port = int(os.environ.get("PORT", 5000))
    # '0.0.0.0' allows external access on Render
    app.run(host='0.0.0.0', port=port)