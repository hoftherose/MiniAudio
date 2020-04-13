# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/Transforms.ipynb (unless otherwise specified).

__all__ = ['NormalizeAudio', 'MuLawEncoding']

# Cell
from fastai2.basics import *
import librosa
import torchaudio

# Cell
class NormalizeAudio(Transform):
    def encodes(self, sig:ndarray):
        return librosa.util.normalize(sig)

# Cell
class MuLawEncoding(Transform):
    order = 11
    def __init__(self, quantization_channels:int=256):
        self.MuLawEnc = torchaudio.transforms.MuLawEncoding(quantization_channels)
        self.MuLawDec = torchaudio.transforms.MuLawDecoding(quantization_channels)
    def encodes(self, sig:Tensor):
        print("enc")
        return self.MuLawEnc(sig)
    def decodes(self, sig:Tensor):
        print("dec")
        return self.MuLawDec(sig)