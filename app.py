from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://intellevo.ai"}})

load_dotenv()
mongo_uri = os.getenv('MONGODB_URI')

if mongo_uri is None:
    raise ValueError("MongoDB URI not found in environment variables")

client = MongoClient(mongo_uri)
db = client['Intellevodb']
waitlist_collection = db.users

gmail_user = os.getenv('GMAIL_USER')
gmail_password = os.getenv('GMAIL_PASSWORD')

if gmail_user is None or gmail_password is None:
    raise ValueError("Gmail credentials not found in environment variables")

def send_confirmation_email(email, name):
    try:
        with open("index.html", "r") as file:
            html_content = file.read()

        html_content = html_content.replace('{name}', name)

        subject = 'Thank you for joining our waitlist! 😊'
        message = MIMEMultipart()
        message['From'] = gmail_user
        message['To'] = email
        message['Subject'] = subject

        message.attach(MIMEText(html_content, 'html'))

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(gmail_user, gmail_password)
            text = message.as_string()
            server.sendmail(gmail_user, email, text)

        print('Confirmation email sent successfully')
    except Exception as e:
        print(f'Error sending confirmation email: {str(e)}')

@app.route('/')
def hello_world():
    return 'Hello, world!'

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()

        name = data.get('name')
        email = data.get('email')

        existing_user = waitlist_collection.find_one({'email': email})
        if existing_user:
            return jsonify({'error': 'User with this email is already registered.'}), 400

        waitlist_collection.insert_one({
            'name': name,
            'email': email,
        })

        send_confirmation_email(email, name)

        return jsonify({'message': 'Form submitted successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run()
