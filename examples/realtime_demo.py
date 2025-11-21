import pyaudio
import numpy as np
from webrtc_audio_all import AudioProcessor

SAMPLE_RATE = 16000  # or 48000
FRAME_MS = 10
CHUNK = int(SAMPLE_RATE * FRAME_MS / 1000)

ap = AudioProcessor(sample_rate=SAMPLE_RATE, enable_aec=True, enable_ns=True, enable_agc=True, enable_vad=False)

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=SAMPLE_RATE, input=True, output=True, frames_per_buffer=CHUNK)
print("Start (Ctrl+C to stop)")
try:
    while True:
        d = stream.read(CHUNK, exception_on_overflow=False)
        arr = np.frombuffer(d, dtype=np.int16)
        out = ap.process(arr)
        stream.write(out.tobytes())
except KeyboardInterrupt:
    print("Stop")
finally:
    stream.stop_stream(); stream.close(); p.terminate()
