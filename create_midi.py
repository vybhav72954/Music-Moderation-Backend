from transcribe import load_model, OnlineTranscriber
import numpy as np
from midiutil import MIDIFile
import base64, io, os
import time as timestamp
import pandas as pd
import wave
import pyaudio
import subprocess as subp

# BPM that should be set by the song user is playing
# upd 6/9/22 - this doesn't really matter because we are using seconds
# we can add a "guess_bpm" method or some shit here
BPM = 60

# chunk size
CHUNK = 512
# SET CLIENT TO PCM 16-BIT
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
    # create a timestamp (for file names)
    ts = timestamp.time()
    # write wav file
    audio_file_name = str(ts) + ".wav"
    # print(audio_bytes)
    with open(audio_file_name, "w+b") as file:
       file.write(audio_bytes)
    # wtf
    # subp.check_call("ffmpeg -i " + audio_file_name + " -acodec pcm_s16le -ac 1 -ar 16000 " + audio_file_name, shell=True)
    # read wav file
    f = wave.open(audio_file_name, "rb")
    # create audio bytestream
    p = pyaudio.PyAudio()
    stream = p.open(format = p.get_format_from_width(f.getsampwidth()),  
                channels = f.getnchannels(),  
                rate = f.getframerate(),  
                output = True)
    # read first chunk of audio
    buffer = f.readframes(CHUNK)
    frame = 0
    # iterate through the audio by chunk
    while buffer:
        # decode data from buffer
        decoded = np.frombuffer(buffer, dtype=np.int16)
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
        buffer = f.readframes(CHUNK)
        frame += 1

    # close pyaudio stream
    stream.stop_stream()
    stream.close()
    p.terminate()

    # save midi file
    midi_file_name = str(ts) + ".mid"
    with open(midi_file_name, "w+b") as output_file:
        MyMIDI.writeFile(output_file)
    
    return midi_file_name

# right now reference midi file name = None and it WILL crash when executed
def extract_errors(user_midi_file_name, reference_midi_file_name):
    # run alignment tool
    # subp.check_call('mv ' + user_midi_file_name + ' AlignmentTool/' + user_midi_file_name + ' && mv ' + reference_midi_file_name + ' AlignmentTool/' + reference_midi_file_name + ' && cd AlignmentTool/ && ./MIDIToMIDIAlign.sh ' + user_midi_file_name[:-4] + ' ' + reference_midi_file_name[:-4] + ' && cd ..', shell=True)
    # load tables into panda
    corresp_file_name = 'AlignmentTool/' + reference_midi_file_name[:-4] + "_corresp.txt"
    corresp_header = ["id", "onset_time", "spelled_pitch", "integer_pitch", "onset_velocity", "reference_id",
                "reference_onset_time", "reference_spelled_pitch", "reference_integer_pitch", "reference_onset_velocity", "blank"]
    corresp_data = pd.read_csv(corresp_file_name, sep='\t', skiprows=[0], names=corresp_header, index_col=0)

    match_file_name = 'AlignmentTool/' + reference_midi_file_name[:-4] + "_match.txt"
    match_header = ["id", "onset_time", "offset_time", "spelled_pitch", "onset_velocity",
                "offset_velocity", "channel", "match_status", "score_time", "note_id",
                "error_index", "skip_index"]
    match_data = pd.read_csv(match_file_name, sep='\t', skiprows=[0,1,2,3], names=match_header, index_col=0)[:-2]

    # this has to be a dictionary of all notes - pitches and time (reference + mistakes)
    # return format:
    # bpm
    # timesig
    # notes: [
    #     measure
    #     pitch_integer
    #     pitch_spelled
    #     onset_time -> seconds from start of measure
    #     length -> note length (like "1/4")
    #     note_type -> "extra, missing, incorrect, reference"
    # ]

    # code below is untested, need audio from Mohamed and reference midi

    reference_bpm = 60 # should come from midi
    reference_timesig_numerator = 4 # should come from midi
    reference_timesig_denominator = 4 # should come from midi
    # measure is time / beats per second * 4 (give 4/4 time signature)
    measure_func = lambda time : time // (reference_bpm/60*4)

    performance_data = {
        'bpm': reference_bpm,
        'timesig': str(reference_timesig_numerator) + "/" + str(reference_timesig_denominator),
        'notes': []
    }

    for idx, row in corresp_data.iterrows():
        # get note info
        pitch_played_spelled = None
        pitch_integer = row['reference_integer_pitch']
        pitch_spelled = row['reference_spelled_pitch']
        onset_time = row['reference_onset_time']
        # !!!!! oh fuck we don't have reference offset here so no length ffs
        measure = measure_func(onset_time)
        note_type = "reference"
        # process extra notes
        if row['reference_id'] == '*':
            note_type = "extra"
            pitch_integer = row['integer_pitch']
            pitch_spelled = row['spelled_pitch']
            onset_time = row['onset_time']
        # process missing notes
        elif idx == '*':
            note_type = "missing"
        # process incorrect pitch
        elif match_data.loc[idx]["error_index"] == 1:
            note_type = "incorrect"
            pitch_played_spelled = match_data.iloc[[idx]]['spelled_pitch']

        note = {
            'measure': measure,
            'pitch_integer': pitch_integer,
            'pitch_spelled': pitch_spelled,
            'pitch_played_spelled': pitch_played_spelled,
            'onset_time': onset_time,
            'length': None,
            'note_type': note_type
        }

        performance_data['notes'].append(note)

    # it would be good to remove generated txt files and the midi files here

    return performance_data

print(extract_errors("test_user.mid", "test_ref.mid"))