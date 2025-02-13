import os

import torch
import torch.nn.functional as F
import webdataset as wds
from pytorch_lightning import Trainer, seed_everything
from pytorch_lightning.tuner.tuning import Tuner
from torch.utils.data import DataLoader

import satflow.models
from satflow.core.training_utils import get_args, get_loaders, setup_experiment
from satflow.core.utils import load_config, make_logger
from satflow.data.datasets import SatFlowDataset
from satflow.models import get_model

logger = make_logger("satflow.train")


def run_experiment(args):
    config = setup_experiment(args)
    config["device"] = (
        ("cuda" if torch.cuda.is_available() else "cpu") if not args.with_cpu else "cpu"
    )

    # Load Model
    model = get_model(config["model"]["name"]).from_config(config["model"])
    # Load Datasets
    loaders = get_loaders(config["dataset"])

    # Get batch size that fits in memory

    # trainer = Trainer(auto_scale_batch_size='power')
    # trainer.tune(model)
    # tuner = Tuner(trainer)

    # new_batch_size = tuner.scale_batch_size(model)
    trainer = Trainer(
        gpus=1,
        auto_lr_find=True,
        max_steps=config["training"]["iterations"],
        min_epochs=0,
        val_check_interval=config["training"]["eval_steps"],
        limit_train_batches=2000,
        limit_val_batches=config["training"]["eval_examples"],
        accumulate_grad_batches=4,
        profiler="simple",
    )

    trainer.tune(model, loaders["train"], loaders["test"])

    trainer.fit(model, loaders["train"], loaders["test"])


if __name__ == "__main__":
    args = get_args()
    run_experiment(args)
