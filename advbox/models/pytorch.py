#coding=utf-8
# Copyright 2017 - 2018 Baidu Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Tensorflow model
"""
from __future__ import absolute_import

import numpy as np
import os

from .base import Model

import logging
logger=logging.getLogger(__name__)


import torchvision
from torch.autograd import Variable

#直接加载pb文件
class PytorchModel(Model):


    def __init__(self,
                 model,
                 loss,
                 bounds,
                 channel_axis=3,
                 preprocess=None):

        import torch


        if preprocess is None:
            preprocess = (0, 1)

        super(PytorchModel, self).__init__(
            bounds=bounds, channel_axis=channel_axis, preprocess=preprocess)


        self._model = model
        self._loss=loss

        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        print(self._device)

        logger.info("Finish PytorchModel init")

    #返回值为标量
    def predict(self, data):
        """
        Calculate the prediction of the data.
        Args:
            data(numpy.ndarray): input data with shape (size,
            height, width, channels).
        Return:
            numpy.ndarray: predictions of the data with shape (batch_size,
                num_of_classes).
        """

        import torch

        scaled_data = self._process_input(data)

        scaled_data = torch.from_numpy(scaled_data).to(self._device)


        # Run prediction
        predict = self._model(scaled_data)
        predict = np.squeeze(predict, axis=0)

        predict=predict.detach()

        predict=predict.cpu().numpy().copy()

        #logging.info(predict)

        return predict

    #返回值为tensor
    def predict_tensor(self, data):
        """
        Calculate the prediction of the data.
        Args:
            data(numpy.ndarray): input data with shape (size,
            height, width, channels).
        Return:
            numpy.ndarray: predictions of the data with shape (batch_size,
                num_of_classes).
        """

        import torch

        scaled_data = self._process_input(data).to(self._device)

        #scaled_data = torch.from_numpy(scaled_data)


        # Run prediction
        predict = self._model(scaled_data)
        #predict = np.squeeze(predict, axis=0)

        #predict=predict.detach()

        #predict=predict.numpy()

        #logging.info(predict)

        return predict

    def num_classes(self):
        """
            Calculate the number of classes of the output label.
        Return:
            int: the number of classes
        """

        return self._nb_classes

    def gradient(self, data, label):
        """
        Calculate the gradient of the cross-entropy loss w.r.t the image.
        Args:
            data(numpy.ndarray): input data with shape (size, height, width,
            channels).
            label(int): Label used to calculate the gradient.
        Return:
            numpy.ndarray: gradient of the cross-entropy loss w.r.t the image
                with the shape (height, width, channel).
        """

        import torch

        scaled_data = self._process_input(data)

        #logging.info(scaled_data)

        scaled_data = torch.from_numpy(scaled_data).to(self._device)
        scaled_data.requires_grad = True

        label = np.array([label])
        label = torch.from_numpy(label).to(self._device)
        #label = torch.Tensor(label).to(self._device)

        output=self.predict_tensor(scaled_data).to(self._device)

        loss=self._loss(output, label)

        #计算梯度
        # Zero all existing gradients
        self._model.zero_grad()
        loss.backward()

        #技巧 梯度也是tensor 需要转换成np
        grad = scaled_data.grad.cpu().numpy().copy()


        return grad.reshape(scaled_data.shape)

    def predict_name(self):
        """
        Get the predict name, such as "softmax",etc.
        :return: string
        """
        return self._predict_program.block(0).var(self._predict_name).op.type
