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
        return response.choices[0].message.content.strip().replace('"', "'") # Replace quotes to avoid HTML breaking
    except Exception as e:
        return f"Hello Member {member_id}, we have a special Loyalty Loan discount for you!"

def run_analysis():
    """Processes data and returns an Executive Summary followed by Action Cards."""
    file_path = 'data/top_50_loyalty_list.csv'
    
    if not os.path.exists(file_path):
        try:
            subprocess.run(["python", "predict.py"], check=True)
        except Exception as e:
            return f"<p style='color:red;'>System Error: {e}</p>"

    try:
        df = pd.read_csv(file_path)
        total_analyzed = len(df)
        
        # Segmenting for the Executive Summary
        critical_count = len(df[df['churn_probability'] > 0.8])
        high_risk_count = len(df[(df['churn_probability'] > 0.5) & (df['churn_probability'] <= 0.8)])
        monitor_count = len(df[(df['churn_probability'] > 0.05) & (df['churn_probability'] <= 0.5)])

        # 1. EXECUTIVE SUMMARY SECTION
        summary_html = f"""
        <div class="alert alert-dark shadow-sm border-0 mb-4" style="background: #1a1a2e; color: white; border-radius: 15px;">
            <div class="row text-center py-2">
                <div class="col-md-3 border-end border-secondary">
                    <small class="text-uppercase opacity-75" style="font-size: 0.7rem;">Members Scanned</small>
                    <h3 class="fw-bold mb-0">{total_analyzed}</h3>
                </div>
                <div class="col-md-3 border-end border-secondary">
                    <small class="text-uppercase text-danger" style="font-size: 0.7rem;">Critical Risk</small>
                    <h3 class="fw-bold mb-0 text-danger">{critical_count}</h3>
                </div>
                <div class="col-md-3 border-end border-secondary">
                    <small class="text-uppercase text-warning" style="font-size: 0.7rem;">High Risk</small>
                    <h3 class="fw-bold mb-0 text-warning">{high_risk_count}</h3>
                </div>
                <div class="col-md-3">
                    <small class="text-uppercase text-info" style="font-size: 0.7rem;">Under Monitor</small>
                    <h3 class="fw-bold mb-0 text-info">{monitor_count}</h3>
                </div>
            </div>
        </div>
        <h4 class="mb-3 fw-bold"><i class="fas fa-bullseye me-2 text-primary"></i>Priority Retention Missions</h4>
        """

        # 2. MEMBER ACTION CARDS SECTION
        df = df.sort_values(by='churn_probability', ascending=False)
        high_risk = df[df['churn_probability'] > 0.05].copy()
        
        if high_risk.empty:
            return summary_html + "<p class='text-muted text-center'>✅ All members are currently stable.</p>"

        html_cards = summary_html
        for _, row in high_risk.iterrows():
            member = int(row['member_id'])
            prob = row['churn_probability'] * 100
            score = row['engagement_score']
            ai_sms = get_ai_recommendation(member, prob, score)
            
            if prob > 80:
                badge, color_class, border_color = "CRITICAL", "bg-danger", "#e74c3c"
            elif prob > 50:
                badge, color_class, border_color = "HIGH RISK", "bg-warning text-dark", "#f39c12"
            else:
                badge, color_class, border_color = "MONITOR", "bg-info text-dark", "#3498db"

            html_cards += f"""
            <div class="card risk-card shadow-sm mb-4" style="border: none; border-radius: 12px; border-left: 8px solid {border_color}; transition: transform 0.2s;">
                <div class="card-body p-4">
                    <div class="d-flex justify-content-between align-items-start mb-3">
                        <div>
                            <h5 class="fw-bold mb-1">Member ID: {member}</h5>
                            <p class="text-muted small mb-0">Analysis complete: Churn probability is {prob:.1f}%</p>
                        </div>
                        <span class="badge {color_class} px-3 py-2">{badge}</span>
                    </div>
                    
                    <div class="row mb-3 bg-light rounded p-3 mx-0">
                        <div class="col-6 border-end">
                            <small class="text-muted d-block text-uppercase" style="font-size: 0.65rem;">Probability</small>
                            <span class="fw-bold h5">{prob:.1f}%</span>
                        </div>
                        <div class="col-6 ps-4">
                            <small class="text-muted d-block text-uppercase" style="font-size: 0.65rem;">Engagement</small>
                            <span class="fw-bold h5">{score:.2f}</span>
                        </div>
                    </div>

                    <div class="p-3 mb-3 bg-white border-start border-3 border-primary rounded shadow-sm" style="font-style: italic; background-color: #f8f9ff !important;">
                        <small class="d-block text-primary fw-bold mb-1"><i class="fas fa-robot me-1"></i> AI AGENT RECOMMENDED MESSAGE:</small>
                        "{ai_sms}"
                    </div>

                    <div class="d-flex gap-2 justify-content-end">
                        <button class="btn btn-outline-secondary btn-sm" onclick="navigator.clipboard.writeText('{ai_sms}')">
                            <i class="fas fa-copy me-1"></i> Copy
                        </button>
                        <a href="https://wa.me/?text={ai_sms}" target="_blank" class="btn btn-success btn-sm px-4">
                            <i class="fab fa-whatsapp me-1"></i> Deploy SMS
                        </a>
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
            if file and file.filename.endswith('.csv'):
                file.save(os.path.join(UPLOAD_FOLDER, 'raw_input.csv'))
                try:
                    subprocess.run(["python", "predict.py"], check=True)
                    status_msg = "✅ Upload successful. Model re-trained."
                except:
                    status_msg = "❌ Error running prediction engine."
            else:
                status_msg = "❌ Invalid file type. Please upload a CSV."

    report_html = run_analysis()
    
    return render_template('dashboard.html', 
                           report_html=report_html, 
                           status_msg=status_msg)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)