import os
import torch

from wandb import Api
from wandb import Artifact

from models.sparse_autoencoder import SparseAutoencoder

entity_name = 'nlp_and_interpretability'
project_prefix = 'Autoencoder_training'
artifact_prefix = 'autoencoders'

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
            model_path = os.path.join(save_dir, f'{model_name}')
            torch.save([model.kwargs, model.state_dict()], model_path)
            print(f"Saved {model_name} to {model_path}")


def save_autoencoders_for_artifact(
        autoencoders_base_big, autoencoders_base_small, autoencoders_rlhf_big, autoencoders_rlhf_small,
        policy_model_name, hyperparameters, alias, run
    ):
    '''
    Saves the autoencoders from one run into memory. Note that these paths are to some extent hardcoded
    '''
    save_dir = 'saves'
    save_models_to_folder(autoencoders_base_big, save_dir=f'{save_dir}/base_big')
    save_models_to_folder(autoencoders_base_small, save_dir=f'{save_dir}/base_small')
    save_models_to_folder(autoencoders_rlhf_big, save_dir=f'{save_dir}/rlhf_big')
    save_models_to_folder(autoencoders_rlhf_small, save_dir=f'{save_dir}/rlhf_small')

    simplified_policy_name = policy_model_name.split('/')[-1].replace("-", "_")
    artifact_name = f'{artifact_prefix}_{simplified_policy_name}'
    saved_artifact = Artifact(artifact_name, metadata=hyperparameters, type='model')
    saved_artifact.add_dir(save_dir, name=save_dir)

    aliases = {simplified_policy_name, 'latest'}
    aliases.add(alias)
    aliases = sorted(list(aliases))
    run.log_artifact(saved_artifact, aliases=aliases)

def load_autoencoders_for_artifact(policy_model_name, alias='latest'):
    '''
    Loads the autoencoders from one run into memory. Note that these paths are to some extent hardcoded
    For example, try autoencoders_dict = load_autoencoders_for_artifact('pythia_70m_sentiment_reward')
    '''
    api = Api()
    simplified_policy_model_name = policy_model_name.split('/')[-1].replace('-', '_')
    full_path = f'{entity_name}/{project_prefix}_{policy_model_name}/{artifact_prefix}_{simplified_policy_model_name}:{alias}'
    print(f'Loading artifact from {full_path}')

    artifact = api.artifact(full_path)
    directory = artifact.download()

    save_dir = f'{directory}/saves'
    autoencoders_base_big = load_models_from_folder(f'{save_dir}/base_big')
    autoencoders_base_small = load_models_from_folder(f'{save_dir}/base_small')
    autoencoders_rlhf_big = load_models_from_folder(f'{save_dir}/rlhf_big')
    autoencoders_rlhf_small = load_models_from_folder(f'{save_dir}/rlhf_small')

    return {
        'base_big': autoencoders_base_big, 'base_small': autoencoders_base_small,
        'rlhf_big': autoencoders_rlhf_big, 'rlhf_small': autoencoders_rlhf_small
    }

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
        kwargs, state = torch.load(model_path)
        model = SparseAutoencoder(**kwargs)
        model.load_state_dict(state)
        model.eval()
        model_dict[model_name] = model
        print(f"Loaded {model_name} from {model_path}")

    return model_dict
