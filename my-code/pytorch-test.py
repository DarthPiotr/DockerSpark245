import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

import torch.multiprocessing as mp
from torch.utils.data.distributed import DistributedSampler
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.distributed import init_process_group, destroy_process_group
import os
import sys

import torch
from torch.utils.data import Dataset

class MyTrainDataset(Dataset):
    def __init__(self, size):
        self.size = size
        self.data = [(torch.rand(20), torch.rand(1)) for _ in range(size)]

    def __len__(self):
        return self.size
    
    def __getitem__(self, index):
        return self.data[index]

def ddp_setup(use_gpu):
    if use_gpu:
        torch.cuda.set_device(int(os.environ["LOCAL_RANK"]))
    backend = "nccl" if use_gpu else "gloo"
    init_process_group(backend=backend)

class Trainer:
    def __init__(
        self,
        model: torch.nn.Module,
        train_data: DataLoader,
        optimizer: torch.optim.Optimizer,
        save_every: int,
        snapshot_path: str,
    ) -> None:
        self.local_rank = int(os.environ["LOCAL_RANK"])
        self.global_rank = int(os.environ["RANK"])
        self.model = model.to(self.local_rank)
        self.train_data = train_data
        self.optimizer = optimizer
        self.save_every = save_every
        self.epochs_run = 0
        # self.snapshot_path = snapshot_path
        # if os.path.exists(snapshot_path):
        #     print("Loading snapshot")
        #     self._load_snapshot(snapshot_path)

        self.model = DDP(self.model, device_ids=[self.local_rank])

    # def _load_snapshot(self, snapshot_path):
    #     loc = f"cuda:{self.local_rank}"
    #     snapshot = torch.load(snapshot_path, map_location=loc)
    #     self.model.load_state_dict(snapshot["MODEL_STATE"])
    #     self.epochs_run = snapshot["EPOCHS_RUN"]
    #     print(f"Resuming training from snapshot at Epoch {self.epochs_run}")

    def _run_batch(self, source, targets):
        self.optimizer.zero_grad()
        output = self.model(source)
        loss = F.cross_entropy(output, targets)
        loss.backward()
        self.optimizer.step()

    def _run_epoch(self, epoch):
        b_sz = len(next(iter(self.train_data))[0])
        print(f"[GPU{self.global_rank}] Epoch {epoch} | Batchsize: {b_sz} | Steps: {len(self.train_data)}")
        self.train_data.sampler.set_epoch(epoch)
        for source, targets in self.train_data:
            source = source.to(self.local_rank)
            targets = targets.to(self.local_rank)
            self._run_batch(source, targets)

    # def _save_snapshot(self, epoch):
    #     snapshot = {
    #         "MODEL_STATE": self.model.module.state_dict(),
    #         "EPOCHS_RUN": epoch,
    #     }
    #     torch.save(snapshot, self.snapshot_path)
    #     print(f"Epoch {epoch} | Training snapshot saved at {self.snapshot_path}")

    def train(self, max_epochs: int):
        for epoch in range(self.epochs_run, max_epochs):
            self._run_epoch(epoch)
            # if self.local_rank == 0 and epoch % self.save_every == 0:
            #     self._save_snapshot(epoch)


def load_train_objs():
    train_set = MyTrainDataset(2048)  # load your dataset
    model = torch.nn.Linear(20, 1)  # load your model
    optimizer = torch.optim.SGD(model.parameters(), lr=1e-3)
    return train_set, model, optimizer


def prepare_dataloader(dataset: Dataset, batch_size: int):
    return DataLoader(
        dataset,
        batch_size=batch_size,
        pin_memory=True,
        shuffle=False,
        sampler=DistributedSampler(dataset)
    )


def main(save_every: int, total_epochs: int, batch_size: int, snapshot_path: str = "snapshot.pt", use_gpu: bool = False):    

    print()
    import socket
    print(f'[{int(os.environ["RANK"])}]', 'hostname                 : ',  socket.gethostname())
    print(f'[{int(os.environ["RANK"])}]', 'sys.version              : ', sys.version )
    print(f'[{int(os.environ["RANK"])}]', 'torch.cuda.is_available(): ', str(torch.cuda.is_available()))
    print(f'[{int(os.environ["RANK"])}]', 'torch.version.cuda       : ',  torch.version.cuda)
    print(f'[{int(os.environ["RANK"])}]', 'torch.cuda.device_count(): ', torch.cuda.device_count())
    
    ddp_setup(use_gpu)
    dataset, model, optimizer = load_train_objs()
    train_data = prepare_dataloader(dataset, batch_size)
    trainer = Trainer(model, train_data, optimizer, save_every, snapshot_path)
    trainer.train(total_epochs)
    destroy_process_group()


# if __name__ == "__main__":
#     import argparse
#     parser = argparse.ArgumentParser(description='simple distributed training job')
#     parser.add_argument('total_epochs', type=int, help='Total epochs to train the model')
#     parser.add_argument('save_every', type=int, help='How often to save a snapshot')
#     parser.add_argument('--batch_size', default=32, type=int, help='Input batch size on each device (default: 32)')
#     args = parser.parse_args()

from pyspark.ml.torch.distributor import TorchDistributor
from pyspark.sql import SparkSession
spark = SparkSession.\
        builder.\
        appName("pyspark-notebook-2").\
        master("spark://spark-master:7077").\
        config("spark.executor.memory", "512m").\
        getOrCreate()
distributor = TorchDistributor(num_processes=2, local_mode=False, use_gpu=False)
distributor.run(main, 10, 20, 50, use_gpu=True) 

#####################################################################