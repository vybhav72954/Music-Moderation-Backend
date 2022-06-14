# Music-Moderation-Backend

## Setup Guide

1. get `python 3.7` (use `miniconda` for environment management)
2. run `$ pip install -r requirements.txt`
3. download `model-180000.pt` and put it in root directory of the project - [link](https://drive.google.com/file/d/12DnYJJ6YKpsoEkXI9fYUTTd4wOeY_rlB/view) (~180MB)
4. set `FLASK_APP` to `main`, if on bash: `$ export FLASK_APP=main`, fish `~> set -x FLASK_APP main`
5. compile `AlignmentTool` - `$ cd AlignmentTool && rm -r Programs && ./compile.sh`
6. run `$ flask run`

## API

|verb|endpoint|request|response|notes|
--- | --- | ---|---|---|
|POST|/api/transcribe|{ "audio": BYTES OF AUDIO }|{ "midi_file": MIDI FILE NAME ON SERVER }|request must me in json, audio should be sent in PCM 16-bit format at 16kHz sampling rate|
|GET|/api/transcribe| { any }|{ "Kidnap": "Influencer", "Subject": "Post Toilet Bowl for me" }|do we even need this?

