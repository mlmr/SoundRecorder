# Instead of adding silence at start and end of recording (values=0) I add the original audio . This makes audio sound more natural as volume is >0. See trim()
# I also fixed issue with the previous code - accumulated silence counter needs to be cleared once recording is resumed.

import os
import platform
from array import array
from struct import pack
from sys import byteorder
import pyaudio
from pydub import AudioSegment
import wave

THRESHOLD = 500  # audio levels not normalised.
CHUNK_SIZE = 1024
SILENT_CHUNKS = 3 * 44100 / 1024  # about 3sec
FORMAT = pyaudio.paInt16
FRAME_MAX_VALUE = 2 ** 15 - 1
NORMALIZE_MINUS_ONE_dB = 10 ** (-1.0 / 20)
RATE = 44100
CHANNELS = 1
TRIM_APPEND = RATE / 4


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

    # def trim(self, data_all):
    #     r = []
    #     if data_all:
    #         _from = 0
    #         _to = len(data_all) - 1
    #         for i, b in enumerate(data_all):
    #             if abs(b) > THRESHOLD:
    #                 _from = max(0, i - TRIM_APPEND)
    #                 break
    #
    #         for i, b in enumerate(reversed(data_all)):
    #             if abs(b) > THRESHOLD:
    #                 _to = min(len(data_all) - 1, len(data_all) - 1 - i + TRIM_APPEND)
    #                 break
    #
    #         r = copy.deepcopy(data_all[int(_from):(int(_to) + 1)])
    #     return r

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
            # little endian, signed short
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
        # print("record_to_file")
        sample_width, data = self.record(None)
        data = pack('<' + ('h' * len(data)), *data)
        # if not os.path.isfile(self.owner.path_to_file):
        # wave_file = wave.open(self.owner.path_to_file, 'wb')
        # wave_file.setnchannels(CHANNELS)
        # wave_file.setsampwidth(sample_width)
        # wave_file.setframerate(RATE)
        # wave_file.writeframes(data)
        # wave_file.close()

        if platform.system() == "Windows":
            AudioSegment.converter = r"C:\\ffmpeg-20200522-38490cb-win64-static\\bin\\ffmpeg.exe"
        sound = AudioSegment(data, frame_rate=RATE, sample_width=sample_width, channels=CHANNELS)

        sound.export(self.owner.path_to_file[:-4] + ".mp3", format="mp3")

        self.owner.check_file_existence()


if __name__ == '__main__':
    audio = Audio(None)
    audio.record_to_file()
