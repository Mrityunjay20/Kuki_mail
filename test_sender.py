import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
from dotenv import load_dotenv
from streamlit_quill import st_quill
import re
from email_validator import validate_email, EmailNotValidError
from pathlib import Path
import time

# Load environment variables
load_dotenv()

def init_session_state():
    if 'email_sent' not in st.session_state:
        st.session_state.email_sent = False
    if 'progress' not in st.session_state:
        st.session_state.progress = 0

def validate_emails(df):
    invalid_emails = []
    for idx, row in df.iterrows():
        try:
            validate_email(row['email'])
        except EmailNotValidError:
            invalid_emails.append(f"Row {idx + 2}: {row['email']}")
    return invalid_emails

# def clean_content(content):
#     # Process line by line to handle tabs and spaces
#     lines = []
#     prev_empty = False
    
#     for line in content.split('\n'):
#         # Convert tabs to spaces while preserving alignment
#         line = line.expandtabs(4)
#         # Keep leading spaces but remove trailing ones
#         line = line.rstrip()
        
#         # Handle empty lines
#         if not line:
#             if not prev_empty:  # Only add <br> if previous line wasn't empty
#                 lines.append('<br>')
#             prev_empty = True
#         else:
#             lines.append(line)
#             prev_empty = False
    
#     # Join lines with spaces (no <br> between consecutive non-empty lines)
#     content = ' '.join(lines)
#     return content

def clean_content(content):
    # Convert all line break indicators to single <br> tags
    content = content.replace('</p><p>', '<br>')  # Handle Quill's paragraph separation
    content = content.replace('<p>', '').replace('</p>', '<br>')  # Remove <p> tags
    content = re.sub(r'<br>\s*<br>', '<br>', content)  # Remove consecutive <br> tags
    return content.strip()

def send_test_email(sender_email, sender_password, subject, content, attachments):
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = sender_email
        msg['Subject'] = "Test Email"
        
        # Clean and format content
        cleaned_content = clean_content(content)
        # Add HTML content with proper styling
        html_content = f"""
<html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .content {{ 
                white-space: pre-line;  # This respects line breaks but collapses multiple spaces
                line-height: 1.4;       # Adjust this to control spacing between lines
                margin: 0;
                padding: 0;
            }}
            .content br {{
                display: block;         # Makes <br> behave like line breaks
                content: "";            # No extra content
                margin-bottom: 0;       # Remove extra spacing
            }}
        </style>
    </head>
    <body>
        <div class="content">{cleaned_content}</div>
    </body>
</html>
"""
        msg.attach(MIMEText(html_content, 'html'))
        
        # Add attachments
        if attachments:
            for file in attachments:
                with open(file.name, 'rb') as f:
                    attachment = MIMEApplication(f.read())
                    attachment.add_header('Content-Disposition', 'attachment', filename=file.name.split('/')[-1])
                    msg.attach(attachment)
        
        # Send email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        return True, "Test email sent successfully!"
    except Exception as e:
        return False, f"Error sending test email: {str(e)}"

def send_bulk_emails(df, sender_email, sender_password, subject_template, content, attachments):
    total_emails = len(df)
    success_count = 0
    
    for idx, row in df.iterrows():
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = row['email']
            
            # Replace variables in subject
            personalized_subject = subject_template.replace('{name}', row['name'])
            msg['Subject'] = personalized_subject
            
            # Clean, personalize and format content
            personalized_content = content.replace('{name}', row['name'])
            cleaned_content = clean_content(personalized_content)
            html_content = f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; }}
                        .content {{ 
                            white-space: pre-wrap !important;
                            line-height: 1;
                        }}
                    </style>
                </head>
                <body>
                    <div class="content">{cleaned_content}</div>
                </body>
            </html>
            """
            msg.attach(MIMEText(html_content, 'html'))
            
            # Add attachments
            if attachments:
                for file in attachments:
                    with open(file.name, 'rb') as f:
                        attachment = MIMEApplication(f.read())
                        attachment.add_header('Content-Disposition', 'attachment', filename=file.name.split('/')[-1])
                        msg.attach(attachment)
            
            # Send email
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            success_count += 1
            st.session_state.progress = (success_count / total_emails)
            time.sleep(0.1)  # Small delay to prevent rate limiting
            
        except Exception as e:
            st.error(f"Error sending email to {row['email']}: {str(e)}")
    
    return success_count

def main():
    st.set_page_config(page_title="Bulk Email Sender", page_icon="📧")
    init_session_state()
    
    st.title("📧 Bulk Email Sender")
    
    # Email Configuration
    with st.expander("Email Configuration", expanded=True):
        sender_email = st.text_input("Sender Email (Gmail)", key="sender_email")
        sender_password = st.text_input("App Password", type="password", help="Use Gmail App Password", key="sender_password")
    
    # File Upload
    uploaded_file = st.file_uploader("Upload file (CSV or Excel with columns: name, email)", type=['csv', 'xlsx', 'xls'])
    if uploaded_file:
        try:
            # Determine file type and read accordingly
            file_extension = uploaded_file.name.split('.')[-1].lower()
            if file_extension == 'csv':
                df = pd.read_csv(uploaded_file)
            else:  # xlsx or xls
                df = pd.read_excel(uploaded_file)
            if not all(col in df.columns for col in ['name', 'email']):
                st.error("File must contain 'name' and 'email' columns!")
                return
        except pd.errors.EmptyDataError:
            st.error("The uploaded file is empty!")
            return
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
            return
        # Validate emails
        invalid_emails = validate_emails(df)
        if invalid_emails:
            st.error("Invalid emails found:")
            for email in invalid_emails:
                st.write(email)
            return
        
        st.success(f"✅ CSV loaded successfully with {len(df)} recipients")
        
        # Email Content
        subject = st.text_input("Email Subject (Use {name} for recipient's name)", 
                              placeholder="Hello {name}!")
        
        st.write("Email Content (Use {name} for recipient's name)")
        content = st_quill(placeholder="Write your email content here...", 
                         html=True)
        
        # File Attachments
        attachments = st.file_uploader("Attach Files", 
                                     accept_multiple_files=True)
        
        col1, col2 = st.columns(2)
        
        # Test Email
        with col1:
            if st.button("Send Test Email"):
                    if not all([sender_email, sender_password, subject, content]):
                        st.error("Please fill in all required fields!")
                    else:
                        success, message = send_test_email(
                            sender_email, sender_password, subject, content, attachments
                        )
                        if success:
                            st.success(message)
            
        # Send Bulk Emails
        with col2:
            if st.button("Send Bulk Emails"):
                if not all([sender_email, sender_password, subject, content]):
                    st.error("Please fill in all required fields!")
                else:
                    progress_bar = st.progress(0)
                    
                    success_count = send_bulk_emails(
                        df, sender_email, sender_password, subject, content, attachments
                    )
                    
                    if success_count == len(df):
                        st.balloons()
                        st.success(f"🎉 Successfully sent {success_count} emails!")
                    else:
                        st.warning(f"Sent {success_count} out of {len(df)} emails")
            
        # Progress Bar
        if st.session_state.progress > 0:
            st.progress(st.session_state.progress)

if __name__ == "__main__":
    main()
