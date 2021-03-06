from scipy.io.wavfile import write

import sys
import numpy as np
import torch

from hparams import create_hparams
from model import Tacotron2
from layers import TacotronSTFT
from train import load_model
from text import text_to_sequence
import glow
sys.modules['glow'] = glow

def synth1(models, text, out):
    hparams = create_hparams()

    checkpoint_path = models + '/checkpoint_800'
    model = load_model(hparams)
    model.load_state_dict(torch.load(checkpoint_path)['state_dict'])
    _ = model.eval()

    waveglow_path = models + '/waveglow'
    waveglow = torch.load(waveglow_path)['model']
    waveglow.cuda()

    for m in waveglow.modules():
      if 'Conv' in str(type(m)):
        setattr(m, 'padding_mode', 'zeros')

    sequence = np.array(text_to_sequence(text, ['basic_cleaners']))[None, :]
    sequence = torch.autograd.Variable(torch.from_numpy(sequence)).cuda().long()
    mel_outputs, mel_outputs_postnet, _, alignments = model.inference(sequence)
    with torch.no_grad():
        audio = 32768.0 * waveglow.infer(mel_outputs_postnet, sigma=0.666)[0]

    audio = audio.cpu().numpy()
    audio = audio.astype('int16')
    write(out, 22050, audio)

synth1("model", "Наступила  душная  январская  ночь  аргентинского  лета.  Черное   небо покрылось звездами", "test.wav")