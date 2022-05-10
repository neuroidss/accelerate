# AUTOGENERATED! DO NOT EDIT! File to edit: . (unless otherwise specified).

__all__ = []

# Cell
import torch
from fastcore.basics import patch
from fastai.metrics import AccumMetric, ActivationType
from fastai.optimizer import Optimizer, OptimWrapper, _convert_params, pytorch_hp_map, _update
from fastai.torch_core import to_device, default_device

# Cell
@patch
def accumulate(self:AccumMetric, learn):
    "Store targs and preds from `learn`, using activation function and argmax as appropriate"
    pred = learn.pred
    if hasattr(learn, "accelerator"):
        pred, learn.y = learn.gather((pred, learn.y))
    if self.activation in [ActivationType.Softmax, ActivationType.BinarySoftmax]:
        pred = F.softmax(pred, dim=self.dim_argmax)
        if self.activation == ActivationType.BinarySoftmax: pred = pred[:, -1]
    elif self.activation == ActivationType.Sigmoid: pred = torch.sigmoid(pred)
    elif self.dim_argmax: pred = pred.argmax(dim=self.dim_argmax)
    if self.thresh:  pred = (pred >= self.thresh)
    self.accum_values(pred,learn.y,learn)

# Cell
@patch
def step(self:Optimizer, closure=None):
    for p,pg,state,hyper in self.all_params(with_grad=True):
        for cb in self.cbs: state = _update(state, cb(p, **{**state, **hyper}))
        self.state[p] = state

# Cell
@patch
def __init__(self:OptimWrapper, params, opt, hp_map=None, convert_groups=True, **kwargs):
    if callable(opt):
        self.opt = opt(_convert_params(params), **kwargs) if convert_groups else opt(params, **kwargs)
    else:
        self.opt = opt
    if hp_map is None: hp_map = pytorch_hp_map
    self.fwd_map = {k: hp_map[k] if k in hp_map else k for k in detuplify_pg(self.opt.param_groups[0]).keys()}
    self.bwd_map = {v:k for k,v in self.fwd_map.items()}
    self.state = defaultdict(dict, {})
    self.frozen_idx = 0

# Cell
@patch
def gather(self:Learner, *items):
    "Gathers a tensor or list of tensors across all devices"
    return self.acelerator.gather(items)

# Cell
@patch
def _set_device(self:Learner, b):
    if hasattr(self, "accelerator"):
        return to_device(b, self.accelerator.device)
    else:
        model_device = torch.device(torch.cuda.current_device()) if next(self.model.parameters()).is_cuda else torch.device('cpu')
        dls_device = getattr(self.dls, 'device', default_device())
        if model_device == dls_device: return to_device(b, dls_device)
        else: return to_device(b, model_device)

# Cell
@patch
def _do_one_batch(self:Learner):
    self.pred = self.model(*self.xb)
    self('after_pred')
    if len(self.yb):
        self.loss_grad = self.loss_func(self.pred, *self.yb)
        self.loss = self.loss_grad.clone()
    self('after_loss')
    if not self.training or not len(self.yb): return
    self('before_backward')
    if hasattr(self, 'accelerator'):
        self.accelerator.backward(self.loss_grad)
    else:
        self.loss_grad.backward()
    self._with_events(self.opt.step, 'step', CancelStepException)
    self.opt.zero_grad()