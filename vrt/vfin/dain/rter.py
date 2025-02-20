import os

import numpy
import torch

from vrt import dictionaries, utils
from . import networks


class RTer:
    def __init__(
            self,
            height, width,
            model_path=None, default_model_dir=None,
            sf=2, resize_hotfix=False,
            net_name='DAIN_slowmotion', rectify=False, useAnimationMethod=False,
            *args, **kwargs
    ):
        torch.backends.cudnn.enabled = True
        torch.backends.cudnn.benchmark = True
        torch.set_grad_enabled(False)
        # Save parameters
        self.sf = sf
        self.resize_hotfix = resize_hotfix
        self.network = net_name
        # Initialize pader
        self.pader = utils.modeling.Pader(
            width, height, 128, extend_func='replication'
        )
        self.dim = self.pader.paded_size
        # Solve for model path
        if model_path is None:
            model_path = os.path.abspath(os.path.join(
                default_model_dir, dictionaries.model_paths['dain']
            ))
        utils.folder.check_model(model_path)
        # Initilize model
        self.model = networks.__dict__[self.network](
            padding=self.pader.slice,
            channel=3, filter_size=4,
            timestep=1/self.sf, rectify=rectify, useAnimationMethod=useAnimationMethod,
            training=False
        ).cuda()
        # Load state dict
        model_dict = self.model.state_dict()
        pretrained_dict = {k: v for k, v in torch.load(model_path).items() if k in model_dict}
        model_dict.update(pretrained_dict)
        self.model.load_state_dict(model_dict)
        self.model.eval()
        # Initialize batch
        self.need_to_init = True

    def get_output_effect(self):
        return {
            'height': 1,
            'width': 1,
            'fps': self.sf
        }

    def ndarray2tensor(self, frame: list):
        frame = torch.from_numpy(frame[0].copy()).cuda()
        frame = frame.permute(2, 0, 1)
        frame = frame.unsqueeze(0)
        frame = frame.float()
        frame /= 255.0
        frame = self.pader.pad(frame)
        return frame

    def tensor2ndarray(self, tensor):
        tensor = torch.stack(tensor)
        if self.resize_hotfix:
            tensor = utils.modeling.resize_hotfix(tensor)
        tensor = tensor.clamp(0.0, 1.0)
        tensor *= 255.0
        tensor = tensor.byte()
        tensor = tensor.permute(0, 2, 3, 1)
        tensor = tensor.cpu().numpy()
        return tensor

    def rt(self, frame, *args, **kwargs):
        if self.need_to_init:
            self.need_to_init = False
            self.tensor_1 = self.ndarray2tensor(frame)
            self.ndarray_1 = frame
            return []
        self.tensor_0, self.tensor_1 = self.tensor_1, self.ndarray2tensor(frame)
        self.ndarray_0, self.ndarray_1 = self.ndarray_1, frame
        I0 = self.tensor_0
        I1 = self.tensor_1
        intermediate_frames = self.model(I0, I1)
        intermediate_frames = self.tensor2ndarray(intermediate_frames)
        return_ = [self.ndarray_0[0], *intermediate_frames]
        if kwargs['duplicate']:
            return_.extend([frame[0], frame[0]])
        return return_
