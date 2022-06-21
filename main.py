## USE PYTHON 3.7
## AMT WILL NOT WORK ON HIGHER VERSION

import os
import asyncio
from flask_sock import Sock
import create_midi

from flask import Flask, jsonify, request, render_template


app = Flask(__name__)
sockets = Sock(app)

HTTP_SERVER_PORT = 5000

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/transcribe', methods=['GET'])
def ReturnJSON():
    if request.method == 'GET':
        data = {
            "Kidnap" : 'Influencer',
            "Subject" : "Post Toilet Bowl for me",
        }

        return jsonify(data)

# api endpoint for mobile app to send audio bytes to
# accepts POST requests with JSON data
# if audio is missing, returns "fuck off"
# data:
#
# audio: bytes
# 
@app.route('/api/transcribe', methods=['POST'])
def transcribe_endpoint():
    # check for JSON content type
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        # get JSON and if it has audio bytes - process it
        json = request.json
        if 'audio' in json:
            # transcribe audio (this is a placeholder)
            user_midi_file_name = create_midi.transcribe_from_string(json['audio'])

            # parse resulting midi to get errors and return extra notes (pitch + time)
            # THIS WILL NOT WORK, NEED REFERENCE FILE
            # user_mistakes = create_midi.extract_errors(user_midi_file_name, reference_midi_file_name=None)

            # this is a dummy temporary return !!!!!
            data = { "midi_file":user_midi_file_name }
            return jsonify(data)

    # else (any error) -> return fuck off
    data = { 'fuck':'off' }
    return jsonify(data)

'''
async def socket(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request) 

    deepgram_socket = await process_audio(ws)

    while True:
        data = await ws.receive_bytes()
        deepgram_socket.send(data)

async def process_audio(fast_socket: web.WebSocketResponse):
    async def get_transcript(data: Dict) -> None:
        if 'channel' in data:
            transcript = data['channel']['alternatives'][0]['transcript']
        
            if transcript:
                await fast_socket.send_str(transcript)
    return 0
'''

if __name__=="__main__":
    loop = asyncio.get_event_loop()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='192.168.1.6')
