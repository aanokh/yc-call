from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def root():
    """Handle requests to the root URL"""
    print("Received request to root URL")
    print("Request method:", request.method)
    print("Request data:", request.get_data())
    return "OK", 200

@app.route("/voice", methods=['GET', 'POST'])
def voice():
    """Respond to incoming phone calls with a 'Hello world' message"""
    print("Received voice request")
    # Start our TwiML response
    resp = VoiceResponse()

    # Read a message aloud to the caller
    resp.say("Hello My friend, Sean Wu. Are you ready for your interview?")

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True, port=3000)