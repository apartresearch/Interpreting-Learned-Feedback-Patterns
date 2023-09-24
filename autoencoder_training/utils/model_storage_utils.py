import os
import torch

from models.sparse_autoencoder import SparseAutoencoder

def save_models_to_folder(model_dict, save_dir):
    """
    Save PyTorch models from a dictionary to a specified directory.

    Args:
        model_dict (dict): A dictionary containing PyTorch models with keys as model names.
        save_dir (str): The directory where models will be saved.
    """
    os.makedirs(save_dir, exist_ok=True)

    for model_name, model_list in model_dict.items():
        for i, model in enumerate(model_list):
            model_path = os.path.join(save_dir, model_name)
            torch.save([model.kwargs, model.state_dict()], model_path)
            print(f"Saved {model_name} to {model_path}")


def load_models_from_folder(load_dir):
    """
    Load PyTorch models from subfolders of a directory into a dictionary where keys are subfolder names.

    Args:
        load_dir (str): The directory from which models will be loaded.

    Returns:
        model_dict (dict): A dictionary where keys are subfolder names and values are PyTorch models.
    """
    model_dict = {}

    for model_name in sorted(os.listdir(load_dir)):
        model_path = os.path.join(load_dir, model_name)
        if os.path.isdir(model_path):
            kwargs, state = torch.load(model_path)
            model = SparseAutoencoder(**kwargs)
            model.load_state_dict(state)
            model.eval()
            model_dict[model_name] = model
            print(f"Loaded {model_name} from {model_path}")

    return model_dict
