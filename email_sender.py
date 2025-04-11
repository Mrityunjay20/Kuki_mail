import streamlit as st
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from jinja2 import Template
from streamlit_quill import st_quill

st.set_page_config(page_title="Smart Email Sender", layout="wide")
st.title("📧 Smart Personalized Email Sender")

st.markdown("""
Upload a CSV with these columns:

- `name`  
- `email`  
- `starting_line`  

Use `{{ name }}` and `{{ starting_line }}` in your message or subject to personalize them.

You'll also have the option to preview your message by sending a test email to yourself.
""")

# Step 1: Upload CSV
uploaded_file = st.file_uploader("📄 Upload Contacts CSV", type="csv")

# Step 2: Gmail Info
your_email = st.text_input("📬 Your Gmail Address")
app_password = st.text_input("🔐 App Password", type="password")

# Step 3: Email Subject
subject = st.text_input("📌 Email Subject (You can use {{ name }} and {{ starting_line }} here too)")

# Step 4: Custom Greeting
greeting_line = st.text_input("👋 Greeting (e.g., Hi {{ name }},)", value="Hi {{ name }},")

# Step 5: Email Body Editor
st.markdown("### 📝 Write Your Email Body")
editor_content = st_quill(placeholder="Start typing your promotional message...", html=True)  # Important: set html=True

# Step 6: Attachments
attachments = st.file_uploader("📎 Upload Attachments (Optional)", type=None, accept_multiple_files=True)

# Function to apply template variables to any text content
def apply_template_variables(content, variables):
    # Replace template placeholders like {{ name }} with actual values
    template = Template(content)
    return template.render(**variables)

# ------------------------------
# Send Test Email Section
# ------------------------------
st.markdown("---")
st.markdown("### 🧪 Send a Test Email")
test_button = st.button("📤 Send Test Email to Myself")

if test_button and your_email and app_password and subject and editor_content:
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(your_email, app_password)

        test_name = "YourName"
        test_line = "This is a sample starting line just for preview."
        
        # Create proper email HTML structure
        # First apply the template variables to the greeting
        personal_vars = {"name": test_name, "starting_line": test_line}
        personalized_greeting = Template(greeting_line).render(**personal_vars)
        
        # Personalize the subject line
        personalized_subject = apply_template_variables(subject, personal_vars)
        
        # Process the main editor content for template variables
        if "{{ starting_line }}" in editor_content:
            editor_content = editor_content.replace("{{ starting_line }}", test_line)
        if "{{ name }}" in editor_content:
            editor_content = editor_content.replace("{{ name }}", test_name)
        
        # Full HTML email with proper structure and styling
        html_email = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333333; }}
                .email-container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .greeting {{ font-size: 16px; margin-bottom: 15px; }}
                /* List styles */
                ul, ol {{ padding-left: 30px; margin: 10px 0; }}
                li {{ margin-bottom: 5px; }}
                strong {{ font-weight: bold; }}
                em {{ font-style: italic; }}
                u {{ text-decoration: underline; }}
            </style>	
        </head>
        <body>
            <div class="email-container">
                <div class="greeting">{personalized_greeting}</div>
                <div class="content">{editor_content}</div>
            </div>
        </body>
        </html>
        """

        msg = MIMEMultipart('alternative')
        msg["From"] = your_email
        msg["To"] = your_email
        msg["Subject"] = f"[TEST] {personalized_subject}"
        
        # Add plain text version (fallback)
        plain_text = f"{personalized_greeting}\n\n{test_line}\n"
        msg.attach(MIMEText(plain_text, 'plain'))
        
        # Add HTML version with proper content type
        msg.attach(MIMEText(html_email, 'html'))

        # Attach files
        for file in attachments:
            file.seek(0)  # Reset file pointer
            part = MIMEBase("application", "octet-stream")
            part.set_payload(file.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f'attachment; filename="{file.name}"')
            msg.attach(part)
            file.seek(0)  # Reset for reuse

        server.sendmail(your_email, your_email, msg.as_string())
        server.quit()
        st.success("✅ Test email sent to your address!")
        
        # Show a preview of the email
        with st.expander("Show Email Preview"):
            st.markdown("### Subject Preview")
            st.code(personalized_subject)
            st.markdown("### HTML Content Preview")
            st.text(html_email[:500] + "..." if len(html_email) > 500 else html_email)

    except Exception as e:
        st.error(f"❌ Error sending test email: {e}")

# ------------------------------
# Bulk Email Section
# ------------------------------
st.markdown("---")
st.markdown("### 🚀 Send to All Recipients")

if uploaded_file and your_email and app_password and subject and editor_content:
    df = pd.read_csv(uploaded_file)
    
    st.write(f"Found {len(df)} recipients in your CSV file")
    
    if st.button("📨 Send Emails to Everyone"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(your_email, app_password)
            
            total_emails = len(df)
            emails_sent = 0
            
            for index, row in df.iterrows():
                name = row["name"]
                to_email = row["email"]
                starting_line = row.get("starting_line", "")
                
                # Create proper email HTML structure
                # First apply the template variables to the greeting
                personal_vars = {"name": name, "starting_line": starting_line}
                personalized_greeting = Template(greeting_line).render(**personal_vars)
                
                # Personalize the subject line
                personalized_subject = apply_template_variables(subject, personal_vars)
                
                # Process the main editor content for template variables
                personalized_content = editor_content
                if "{{ starting_line }}" in personalized_content:
                    personalized_content = personalized_content.replace("{{ starting_line }}", starting_line)
                if "{{ name }}" in personalized_content:
                    personalized_content = personalized_content.replace("{{ name }}", name)
                
                # Full HTML email with proper structure and styling
                html_email = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333333; }}
                        .email-container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                        .greeting {{ font-size: 16px; margin-bottom: 15px; }}
                        /* List styles */
                        ul, ol {{ padding-left: 30px; margin: 10px 0; }}
                        li {{ margin-bottom: 5px; }}
                        strong {{ font-weight: bold; }}
                        em {{ font-style: italic; }}
                        u {{ text-decoration: underline; }}
                    </style>	
                </head>
                <body>
                    <div class="email-container">
                        <div class="greeting">{personalized_greeting}</div>
                        <div class="content">{personalized_content}</div>
                    </div>
                </body>
                </html>
                """
                
                msg = MIMEMultipart('alternative')
                msg["From"] = your_email
                msg["To"] = to_email
                msg["Subject"] = personalized_subject
                
                # Add plain text version (fallback)
                plain_text = f"{personalized_greeting}\n\n{starting_line}\n"
                msg.attach(MIMEText(plain_text, 'plain'))
                
                # Add HTML version with proper content type
                msg.attach(MIMEText(html_email, 'html'))
                
                # Attach files
                for file in attachments:
                    file.seek(0)  # Reset file pointer
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(file.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f'attachment; filename="{file.name}"')
                    msg.attach(part)
                    file.seek(0)  # Reset for reuse
                
                server.sendmail(your_email, to_email, msg.as_string())
                
                # Update progress
                emails_sent += 1
                status_text.text(f"✅ Email sent to {name} ({to_email})")
                progress_bar.progress(emails_sent / total_emails)
            
            server.quit()
            st.balloons()
            st.success("🎉 All emails sent successfully!")
            
        except Exception as e:
            st.error(f"❌ Error: {e}")
            
else:
    st.info("Fill all the fields, upload your CSV, and you're good to go!")