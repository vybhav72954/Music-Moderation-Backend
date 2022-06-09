import os
import asyncio

from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

async def process_audio(fast_socket: web.WebSocketResponse):
    async def get_transcript(data: Dict) -> None:
        if 'channel' in data:
            transcript = data['channel']['alternatives'][0]['transcript']
        
            if transcript:
                await fast_socket.send_str(transcript)
    return 0



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/listen', methods = ['GET'])
def ReturnJSON():
    if (request.method=='GET'):
        data = {
            "Kidnap":'Influencer',
            "Subject":"Post Toilet Bowl for me",
        }

        return jsonify(data)

'''
async def socket(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request) 

    deepgram_socket = await process_audio(ws)

    while True:
        data = await ws.receive_bytes()
        deepgram_socket.send(data)
'''

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='localhost', port=5000, debug=True)
