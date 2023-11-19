
"""
This class is responsible for extracting feature dictionaries from models,
given hyperparameters and input texts.
"""

import torch
import torch.optim as optim
import torch.nn as nn
from tqdm import tqdm
import wandb

from models.sparse_autoencoder import SparseAutoencoder
from sparse_codes_training.network_helper_functions import get_layer_activations


class AutoencoderDataPreparerAndTrainer:
    """
    The feature extractor is a thin layer on top of sparse autoencoders,
    that gets layer activations from a model on text, and then passes those through
    the autoencoders.
    """
    def __init__(
            self, model, tokenizer, hyperparameters: dict, autoencoder_device: str, model_device: str):
        self.model = model
        self.tokenizer = tokenizer
        self.hyperparameters = hyperparameters

        self.autoencoder_device = autoencoder_device
        self.model_device = model_device

    def train_autoencoder_on_text_activations(
        self, layer_name: str, input_texts: list[str],
        hidden_size_multiple: int, label: str ='default',
    ):
        batch_size = self.hyperparameters['batch_size']

        # Get batch without popping
        first_batch = input_texts[:batch_size].copy()

        first_activations_tensor = get_layer_activations(
            model=self.model, tokenizer=self.tokenizer, layer_name=layer_name, input_texts=first_batch,
            device=self.model_device, hyperparameters=self.hyperparameters
        ).detach().clone().squeeze(1)

        input_size = first_activations_tensor.size(-1)
        print(f'Input size is {input_size}.')

        local_label = f'{layer_name}_{label}_{i}'
        hidden_size = input_size * hidden_size_multiple
        autoencoder = SparseAutoencoder(
            input_size, hidden_size=hidden_size,
            l1_coef=self.hyperparameters['l1_coef'].to(self.autoencoder_device)
        )

        autoencoder.train_model(
                input_texts=input_texts, hyperparameters=self.hyperparameters,
                model_device=self.model_device, autoencoder_device=self.autoencoder_device,
                label=local_label, layer_name=layer_name, model=self.model, tokenizer=self.tokenizer
        )

        return [autoencoder]