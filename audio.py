import platform
from array import array
from struct import pack
from sys import byteorder
import pyaudio
from pydub import AudioSegment

CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
FRAME_MAX_VALUE = 2 ** 15 - 1
NORMALIZE_MINUS_ONE_dB = 10 ** (-1.0 / 20)
RATE = 44100
CHANNELS = 1

class Audio:
    def __init__(self, owner):
        self.owner = owner

    def normalize(self, data_all):
        """Amplify the volume out to max -1dB"""
        # MAXIMUM = 16384
        if data_all:
            maxim = max(abs(i) for i in data_all)
            if maxim < 0.0000001:
                maxim = 0.0000001
            normalize_factor = (float(NORMALIZE_MINUS_ONE_dB * FRAME_MAX_VALUE) / maxim)
        r = array('h')
        for i in data_all:
            r.append(int(i * normalize_factor))
        return r

    def record(self, event):
        """Record a word or words from the microphone and
        return the data as an array of signed shorts."""

        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        output=True,
                        frames_per_buffer=CHUNK_SIZE)

        data_all = array('h')

        self.owner.recording = True
        while self.owner.recording:
            data_chunk = array('h', stream.read(CHUNK_SIZE))
            if byteorder == 'big':
                data_chunk.byteswap()
            data_all.extend(data_chunk)

        sample_width = p.get_sample_size(FORMAT)
        stream.stop_stream()
        stream.close()
        p.terminate()

        data_all = self.normalize(data_all)
        return sample_width, data_all

    def record_to_file(self):
        "Records from the microphone and outputs the resulting data to 'path'"
        sample_width, data = self.record(None)
        data = pack('<' + ('h' * len(data)), *data)

        if platform.system() == "Windows":
            AudioSegment.converter = r"C:\\ffmpeg-20200522-38490cb-win64-static\\bin\\ffmpeg.exe"

        sound = AudioSegment(data, frame_rate=RATE, sample_width=sample_width, channels=CHANNELS)

        sound.export(self.owner.path_to_file[:-4] + ".mp3", format="mp3")

        self.owner.check_file_existence()
