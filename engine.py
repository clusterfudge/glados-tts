import sys
import os
import io
from hashlib import sha256
sys.path.insert(0, os.getcwd() + '/glados_tts')
from glados import TTSRunner
import logging
logging.info("\033[1;94mINFO:\033[;97m Initializing TTS Engine...")

glados = TTSRunner(False, True)


def cache_filename(utterance, root):
    h = sha256(utterance.encode("utf-8")).hexdigest()
    return os.path.join(root, f"{h}.wav")


def cache(utterance, audio, root=os.path.join(os.getcwd(), 'cache')):
    cache_file = cache_filename(utterance, root)
    with open(cache_file, 'wb') as f:
        audio.seek(0)
        f.write(audio.read())


def from_cache(utterance, root=os.path.join(os.getcwd(), 'cache')):
    cache_file = cache_filename(utterance, root)
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            return f.read()
    return None


def glados_tts(text, key=False, alpha=1.0):
    output_buffer = io.BytesIO()
    glados.run_tts(text, alpha).export(output_buffer, format="wav")
    output_buffer.seek(0)
    return output_buffer


# If the script is run directly, assume remote engine
if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    # Remote Engine Variables
    PORT = os.getenv("PORT") or 8124
    CACHE = os.getenv("CACHE") != "FALSE"
    if CACHE:
        logging.info(f"Cache enabled: {os.path.join(os.getcwd(), 'cache')}")
        os.makedirs(os.path.join(os.getcwd(), 'cache'), exist_ok=True)

    from flask import Flask, Response, request

    logging.info("\033[1;94mINFO:\033[;97m Initializing TTS Server...")

    app = Flask(__name__)


    @app.route('/synthesize', methods=['POST'])
    def synthesize():
        text = request.get_data(as_text=True)
        if not text:
            return 'No input', 400

        result = b''
        if CACHE:
            logging.info(f"Checking cache for {text}")
            result = from_cache(text)
            if result:
                logging.info("Cache hit!")
            else:
                logging.info("Cache miss!")

        if not result:
            # Generate New Sample
            audio_buffer = glados_tts(text)
            result = audio_buffer.read()
            if CACHE:
                cache(utterance=text, audio=audio_buffer)

        return Response(result, mimetype="audio/wav")


    cli = sys.modules['flask.cli']
    cli.show_server_banner = lambda *x: None
    app.logger.setLevel(logging.INFO)
    app.run(host="0.0.0.0", port=PORT)
