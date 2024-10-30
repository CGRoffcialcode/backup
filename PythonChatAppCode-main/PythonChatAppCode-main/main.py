import signal
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import google.generativeai as genai
import os
import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS

# Initialize Firebase
cred = credentials.Certificate('chatapp-439018-42db557e6c2a.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# Configure Google Gemini API
genai.configure(api_key="AIzaSyDPzTD6mAd22ZIJ-DxnfYSKNttzMf8fffw")

@app.route('/send-message', methods=['POST'])
def send_message():
    data = request.get_json()
    message = data['message']
    timestamp = datetime.datetime.now().timestamp()  # Get current timestamp

    # Save user message with timestamp
    db.collection('messages').add({'message': message, 'sender': 'user', 'timestamp': timestamp})

    # Get AI response from Google Gemini
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(f"User: {message}\nAI:")
    ai_message = response.text.strip()  # Define ai_message here

    # Save AI response to Firestore
    db.collection('messages').add({'message': ai_message, 'sender': 'ai', 'timestamp': timestamp})

    return jsonify({'status': 'Message sent', 'ai_message': ai_message})


@app.route('/get-messages', methods=['GET'])
def get_messages():
    messages = db.collection('messages').stream()
    messages_list = []
    for msg in messages:
        msg_dict = msg.to_dict()
        # Include timestamp in the response
        messages_list.append({
            'message': msg_dict['message'], 
            'sender': msg_dict['sender'], 
            'timestamp': msg_dict['timestamp'] 
        })
    return jsonify(messages_list)


def delete_all_messages():
    messages = db.collection('messages').stream()
    for msg in messages:
        msg.reference.delete()

def signal_handler(sig, frame):
    print('Shutting down, deleting all messages...')
    delete_all_messages()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True) 

