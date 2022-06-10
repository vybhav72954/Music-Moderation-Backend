from transcribe import load_model, OnlineTranscriber
import numpy as np
from midiutil import MIDIFile
import base64, io, os
import time as timestamp
import pandas as pd

# BPM that should be set by the song user is playing
# upd 6/9/22 - this doesn't really matter because we are using seconds
# we can add a "guess_bpm" method or some shit here
BPM = 60

# chunk size
CHUNK = 512
# audio format
# upd 6/9/22 - need to validate this format with whatever is coming from client
# SET CLIENT TO PCM 16-BIT
FORMAT = pyaudio.paInt16
# get information about microphone channels - MONO
CHANNELS = 1
# sampling rate
# SET CLIENT TO 16kHz
RATE = 16000

# base64 encoded string comes in as input from JSON
# DOES NOT WORK NECESSARILY
def transcribe_from_string(audio_string):
    # load model and transcriber
    model = load_model('model-180000.pt')
    transcriber = OnlineTranscriber(model, return_roll=False)
    # create a midi file to record to
    MyMIDI = MIDIFile(1)
    # set tempo of the midi file
    MyMIDI.addTempo(0, 0, BPM)
    # decode audio
    audio_bytes = base64.b64decode(audio_string)
    # create audio bytestream
    audio_stream = io.BytesIO(audio_bytes)
    # read first chunk
    buffer = audio_stream.read(CHUNK)
    frame = 0
    # iterate through the audio by chunk
    while buffer:
        # decode data from buffer
        decoded = np.frombuffer(buffer, dtype=np.int16) / 32768
        # transcribe the audio to see what what notes came on and off
        frame_output = transcriber.inference(decoded)
        # when model detects onset of a note
        # write it into the midi file
        for pitch in frame_output[0]:
            # correct the pitch output from the model
            pitch = pitch+21
            # set time in beats to where the note should be inserted
            time = (CHUNK/RATE) * frame * BPM/60
            # insert note into midi: track? 0, instrument? 0, pitch, time in beats, 1/16 note, velocity 64
            MyMIDI.addNote(0, 0, pitch, time, 1/4, 64)
            # print note information
            print(pitch, time)
        # read next chunk
        buffer = audio_stream.read(CHUNK)
        frame += 1

    # save midi file
    ts = timestamp.time()
    midi_file_name = str(ts) + ".mid"
    with open(midi_file_name, "w+b") as output_file:
        MyMIDI.writeFile(output_file)
    
    return midi_file_name

# right now reference midi file name = None and it WILL crash when executed
def extract_errors(midi_file_name, reference_midi_file_name):
    # run alignment tool
    os.system('mv {user_file_name} AlignmentTool/{user_file_name} && mv {reference_file_name} AlignmentTool/{reference_file_name} && cd AlignmentTool/ && ./MIDIToMIDIAlign.sh {user_file_name}[:-4] {reference_file_name}[:-4] && cd ..')
    # load tables into panda
    corresp_file_name = reference_file_name[:-4] + "_corresp.txt"
    corresp_header = ["id", "onset_time", "spelled_pitch", "integer_pitch", "onset_velocity", "reference_id",
                "reference_onset_time", "reference_spelled_pitch", "reference_integer_pitch", "reference_onset_velocity", "blank"]
    corresp_data = pd.read_csv(corresp_file_name, sep='\t', skiprows=[0], names=corresp_header, index_col=0)

    match_file_name = reference_file_name[:-4] + "_match.txt"
    match_header = ["id", "onset_time", "offset_time", "spelled_pitch", "onset_velocity",
                "offset_velocity", "channel", "match_status", "score_time", "note_id",
                "error_index", "skip_index"]
    match_data = pd.read_csv(match_file_name, sep='\t', skiprows=[0,1,2,3], names=match_header, index_col=0)[:-2]

    # extra notes - only need user onset time and spelled pitch
    extra_notes = match_data[match_data['error_index'] == 3]

    # missing notes - only need reference onset time and spelled pitch
    missing_notes = corresp_data[corresp_data.index == '*']

    # notes with incorrect pitch only need reference onset time and spelled pitch
    incorrect_notes = match_data[match_data['error_index'] == 1]

    # incorrect/missing pauses
    pause_data = aligned_data[['onset_time', 'reference_onset_time']]
    pause_data['time_diff'] = pause_data.reference_onset_time - pause_data.onset_time

    # this has to be a dictionary of all mistakes - pitches and time (user/reference)
    return { 'mistakes': 'exist' }
