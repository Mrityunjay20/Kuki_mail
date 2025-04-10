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

Use `{{ name }}` and `{{ starting_line }}` in your message to personalize it.

You'll also have the option to preview your message by sending a test email to yourself.
""")

# Step 1: Upload CSV
uploaded_file = st.file_uploader("📄 Upload Contacts CSV", type="csv")

# Step 2: Gmail Info
your_email = st.text_input("📬 Your Gmail Address")
app_password = st.text_input("🔐 App Password", type="password")

# Step 3: Email Subject
subject = st.text_input("📌 Email Subject")

# Step 4: Custom Greeting
greeting_line = st.text_input("👋 Greeting (e.g., Hi {{ name }},)", value="Hi {{ name }},")

# Step 5: Email Body Editor
st.markdown("### 📝 Write Your Email Body")
editor_content = st_quill(placeholder="Start typing your promotional message...")

# Step 6: Attachments
attachments = st.file_uploader("📎 Upload Attachments (Optional)", type=None, accept_multiple_files=True)

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

        template = Template(greeting_line + "<br><br>" + editor_content)
        test_html = template.render(name=test_name, starting_line=test_line)

        msg = MIMEMultipart()
        msg["From"] = your_email
        msg["To"] = your_email
        msg["Subject"] = f"[TEST] {subject}"
        msg.attach(MIMEText(test_html, "html"))

        for file in attachments:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(file.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f'attachment; filename="{file.name}"')
            msg.attach(part)

        server.sendmail(your_email, your_email, msg.as_string())
        server.quit()
        st.success("✅ Test email sent to your address!")

    except Exception as e:
        st.error(f"❌ Error sending test email: {e}")

# ------------------------------
# Bulk Email Section
# ------------------------------
st.markdown("---")
st.markdown("### 🚀 Send to All Recipients")

if uploaded_file and your_email and app_password and subject and editor_content:
    df = pd.read_csv(uploaded_file)

    if st.button("📨 Send Emails to Everyone"):
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(your_email, app_password)

            for index, row in df.iterrows():
                name = row["name"]
                to_email = row["email"]
                starting_line = row.get("starting_line", "")

                # Merge all content using Jinja2
                template = Template(greeting_line + "<br><br>" + editor_content)
                personalized_html = template.render(name=name, starting_line=starting_line)

                msg = MIMEMultipart()
                msg["From"] = your_email
                msg["To"] = to_email
                msg["Subject"] = subject

                msg.attach(MIMEText(personalized_html, "html"))

                # Attach files
                for file in attachments:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(file.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f'attachment; filename="{file.name}"')
                    msg.attach(part)

                server.sendmail(your_email, to_email, msg.as_string())
                st.success(f"✅ Email sent to {name} ({to_email})")

            server.quit()
            st.balloons()
            st.success("🎉 All emails sent successfully!")

        except Exception as e:
            st.error(f"❌ Error: {e}")

else:
    st.info("Fill all the fields, upload your CSV, and you're good to go!")
