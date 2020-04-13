# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/Layers.ipynb (unless otherwise specified).

__all__ = ['Invertible1x1Conv', 'WeightedConv1d', 'WaveNetLayer', 'WaveNet']

# Cell
from fastai2.basics import *

# Cell
class Invertible1x1Conv(torch.nn.Module):
    """
    The layer outputs both the convolution, and the log determinant
    of its weight matrix.  If reverse=True it does convolution with
    inverse
    """

    def __init__(self, c):
        super(Invertible1x1Conv, self).__init__()
        self.conv = torch.nn.Conv1d(c, c, kernel_size=1, stride=1, padding=0,
                                    bias=False)

        # Sample a random orthonormal matrix to initialize weights
        W = torch.qr(torch.FloatTensor(c, c).normal_())[0]

        # Ensure determinant is 1.0 not -1.0
        if torch.det(W) < 0:
            W[:, 0] = -1 * W[:, 0]
        W = W.view(c, c, 1)
        self.conv.weight.data = W

    def forward(self, z, reverse=False):
        # shape
        batch_size, group_size, n_of_groups = z.size()

        W = self.conv.weight.squeeze()

        if reverse:
            if not hasattr(self, 'W_inverse'):
                # Reverse computation
                W_inverse = W.inverse()
                W_inverse = Variable(W_inverse[..., None])
                if z.type() == 'torch.cuda.HalfTensor' or z.type() == 'torch.HalfTensor':
                    W_inverse = W_inverse.half()
                self.W_inverse = W_inverse
            z = F.conv1d(z, self.W_inverse, bias=None, stride=1, padding=0)
            return z
        else:
            # Forward computation
            log_det_W = torch.logdet(W)
            log_det_W = batch_size * n_of_groups * log_det_W
            if z.dtype == torch.float16:
                z = self.conv(z.float()).half()
            else:
                z = self.conv(z)
            return z, log_det_W

# Cell
@delegates(torch.nn.Conv1d)
def WeightedConv1d(in_channels, out_channels, kernel_size, **kwargs):
    layer = nn.Conv1d(in_channels, out_channels, kernel_size, **kwargs)
    return torch.nn.utils.weight_norm(layer, name='weight')

# Cell
class WaveNetLayer(torch.nn.Module):
    """
    Traditional WaveNet Layer which outputs both the residual value and the output.
    """
    def __init__(self, n_mel_channels, kernel_size, dilation, padding):
        super(WaveNetLayer, self).__init__()
        self.SigmDilation = WeightedConv1d(n_mel_channels, n_mel_channels//2, kernel_size,
                                           dilation=dilation, padding=padding)
        self.TanhDilation = WeightedConv1d(n_mel_channels, n_mel_channels//2, kernel_size,
                                           dilation=dilation, padding=padding)
        self.ResLinear = torch.nn.Conv1d(n_mel_channels//2,n_mel_channels, 1, stride=1)
        self.OutLinear = torch.nn.Conv1d(n_mel_channels//2,n_mel_channels, 1, stride=1)
    def forward(self, x):
        sigm_output = torch.nn.Sigmoid()(self.SigmDilation(x))
        tanh_output = torch.nn.Tanh()(self.TanhDilation(x))
        prod = torch.mul(sigm_output, tanh_output)
        out = self.OutLinear(prod)
        res = self.ResLinear(prod)+x
        return out, res

# Cell
class WaveNet(torch.nn.Module):
    def __init__(self, n_mel_channels, precision, n_layers, kernel_size):
        super(WaveNet, self).__init__()
        store_attr(self, 'n_mel_channels, precision, n_layers, kernel_size')
        self.upsample = torch.nn.ConvTranspose1d(n_mel_channels,n_mel_channels,1024, stride=512)
        self.WaveNetLayers = torch.nn.ModuleList()
        for i in range(self.n_layers):
            dilation = 2 ** i
            padding = int((kernel_size * dilation - dilation) / 2)
            self.WaveNetLayers.append(WaveNetLayer(n_mel_channels, kernel_size, dilation, padding))
        self.end = torch.nn.Sequential(torch.nn.ReLU(),torch.nn.Conv1d(n_mel_channels,n_mel_channels*2, 1),
                                       torch.nn.ReLU(),torch.nn.Conv1d(n_mel_channels*2,precision, 1),
                                       torch.nn.Softmax(dim=1))

    def forward(self, spec):
        x = self.upsample(spec)
        for i in range(self.n_layers):
            out, x = self.WaveNetLayers[i](x)
            if i == 0: output = out
            else:      output = out+output
        return self.end(output)