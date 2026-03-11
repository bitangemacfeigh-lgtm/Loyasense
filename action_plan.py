import os
import pandas as pd
import subprocess
from flask import Flask, request, render_template

# Robust Mistral Import
try:
    from mistralai import Mistral
except ImportError:
    from mistralai.client import MistralClient as Mistral

app = Flask(__name__)

# --- CONFIGURATION ---
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "QiJh8V2kZ3IQL1eYCAnKqJSOJxSHbTyC")
UPLOAD_FOLDER = 'data'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Initialize client
try:
    client = Mistral(api_key=MISTRAL_API_KEY)
except Exception as e:
    print(f"Initialization Error: {e}")
    client = None

def get_ai_recommendation(member_id, prob, score):
    """Calls Mistral API for personalized SMS."""
    if not client:
        return f"Hello Member {member_id}, visit our branch for a special Loyalty Loan offer today!"

    prompt = f"""
    Act as a Financial Retention Genius. 
    Member ID: {member_id} | Churn Risk: {prob:.1f}% | Engagement: {score:.2f}
    Task: Write a 1-sentence personalized SMS offer. 
    - If Risk > 50%: Offer 'Priority Loyalty Loan' (3% discount).
    - If Risk < 50%: Offer 'Standard Loyalty Loan' (1.5% discount).
    Tone: Professional and urgent.
    """
    try:
        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Hello Member {member_id}, we have a special Loyalty Loan discount for you!"

def run_analysis():
    """Processes data and returns color-coded HTML results."""
    file_path = 'data/top_50_loyalty_list.csv'
    
    if not os.path.exists(file_path):
        try:
            subprocess.run(["python", "predict.py"], check=True)
        except Exception as e:
            return f"<p style='color:red;'>System Error: {e}</p>"

    try:
        df = pd.read_csv(file_path)
        df = df.sort_values(by='churn_probability', ascending=False)
        high_risk = df[df['churn_probability'] > 0.05].copy()
        
        if high_risk.empty:
            return "<p class='text-muted'>✅ All members are currently stable.</p>"

        html_cards = ""
        for _, row in high_risk.iterrows():
            member = int(row['member_id'])
            prob = row['churn_probability'] * 100
            score = row['engagement_score']
            ai_sms = get_ai_recommendation(member, prob, score)
            
            # Priority Badges and Styles
            if prob > 80:
                badge, color_class, border_color = "CRITICAL", "bg-danger", "#e74c3c"
            elif prob > 50:
                badge, color_class, border_color = "HIGH RISK", "bg-warning text-dark", "#f39c12"
            else:
                badge, color_class, border_color = "MONITOR", "bg-info text-dark", "#3498db"

            html_cards += f"""
            <div class="card risk-card shadow-sm" style="border-left: 6px solid {border_color};">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <h5 class="mb-0">Member {member}</h5>
                        <span class="badge {color_class}">{badge}</span>
                    </div>
                    <p class="small text-muted mb-3">
                        Churn Risk: <strong>{prob:.1f}%</strong> | Engagement Score: <strong>{score:.2f}</strong>
                    </p>
                    <div class="sms-quote">
                        <i class="fas fa-comment-dots me-2 text-primary"></i>"{ai_sms}"
                    </div>
                </div>
            </div>
            """
        return html_cards
    except Exception as e:
        return f"<div class='alert alert-danger'>Data Error: {e}</div>"

@app.route('/', methods=['GET', 'POST'])
def index():
    status_msg = ""
    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            if file.filename.endswith('.csv'):
                # In your predict.py, ensure it reads 'data/raw_input.csv'
                file.save(os.path.join(UPLOAD_FOLDER, 'raw_input.csv'))
                try:
                    subprocess.run(["python", "predict.py"], check=True)
                    status_msg = "✅ Upload successful. Model re-trained."
                except:
                    status_msg = "❌ Error running prediction engine."
            else:
                status_msg = "❌ Invalid file type. Please upload a CSV."

    report_html = run_analysis()
    
    # Passing the variables to your new dashboard.html file
    return render_template('dashboard.html', 
                           report_html=report_html, 
                           status_msg=status_msg)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)