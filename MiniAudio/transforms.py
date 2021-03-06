# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/Transforms.ipynb (unless otherwise specified).

__all__ = ['NormalizeAudio', 'MuLawEncoding', 'get_pitch', 'frequency_order', 'Stft2d']

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
    def __init__(self, precision:int=256):
        self.OneHot = partial(torch.nn.functional.one_hot, num_classes=precision)
        self.MuLawEnc = torchaudio.transforms.MuLawEncoding(precision)
        self.MuLawDec = torchaudio.transforms.MuLawDecoding(precision)
    def encodes(self, sig:Tensor):
        mulaw = self.MuLawEnc(sig)
        return self.OneHot(mulaw)
    def decodes(self, enc:Tensor):
        mulaw = torch.argmax(enc, dim=-2)
        return self.MuLawDec(mulaw)

# Cell
def get_pitch(S):
    return librosa.estimate_tuning(S=S[0], sr=44100)

def frequency_order(specs, attempt=0):
    pitch = L(specs).map(get_pitch)
    order = pitch.zipwith(specs).sorted(lambda x: x[0])
    return order.itemgot(1)

# Cell
class Stft2d(ItemTransform):
    def encodes(self, audio):
        spec = librosa.stft(audio)
        spec = np.pad(spec[:1024,:], ((0,0),(0,8)))
        spec = np.log2(1+abs(spec))
        return np.expand_dims(spec, axis=0)
    def encodes(self, audios:list):
        specs = []
        for audio in audios: specs.append(self.encodes(audio))
        specs = frequency_order(specs)
        return np.concatenate(specs, axis=0)