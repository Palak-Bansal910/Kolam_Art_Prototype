# train_kolam.py
import os, json, random
import numpy as np
from glob import glob
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader

class KolamDataset(Dataset):
    def __init__(self, data_dir, max_len=400):
        self.files = glob(os.path.join(data_dir,"kolam_*.json"))
        self.max_len = max_len

    def __len__(self):
        return len(self.files)

    def __getitem__(self, idx):
        j = json.load(open(self.files[idx]))
        seq = np.array(j["seq"], dtype=np.float32)  # N x 3
        # pad/truncate
        L = seq.shape[0]
        if L > self.max_len:
            seq = seq[:self.max_len]
            L = self.max_len
        pad = np.zeros((self.max_len - L, 3), dtype=np.float32)
        seq_p = np.vstack([seq, pad])
        return seq_p, L

def collate_fn(batch):
    seqs = np.stack([b[0] for b in batch])
    lengths = np.array([b[1] for b in batch])
    return torch.tensor(seqs), torch.tensor(lengths)

class StrokeLSTM(nn.Module):
    def __init__(self, input_size=3, hidden=256, num_layers=2):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden, 3)  # dx, dy, pen_logit

    def forward(self, x, lengths=None):
        # x: B x T x 3
        out, _ = self.lstm(x)
        out = self.fc(out)  # B x T x 3
        return out

def train_epoch(model, opt, dataloader, device):
    model.train()
    total_loss = 0
    for seqs, lengths in dataloader:
        seqs = seqs.to(device)  # B x T x 3
        inputs = seqs.clone()
        targets = seqs.clone()
        # teacher forcing: input at t -> predict t+1
        inputs[:,1:,:] = seqs[:,:-1,:]
        inputs[:,0,:] = 0.0
        preds = model(inputs)
        dxdy_pred = preds[:,:,:2]
        pen_pred = preds[:,:,2]
        dxdy_tgt = targets[:,:,:2]
        pen_tgt = targets[:,:,2]
        loss_l2 = ((dxdy_pred - dxdy_tgt)**2).mean()
        loss_bce = nn.BCEWithLogitsLoss()(pen_pred, pen_tgt)
        loss = loss_l2 + 10.0 * loss_bce
        opt.zero_grad()
        loss.backward()
        opt.step()
        total_loss += loss.item()
    return total_loss / len(dataloader)

def save_model(m, path):
    torch.save(m.state_dict(), path)

def main():
    data_dir = "data_kolam"
    ds = KolamDataset(data_dir)
    dl = DataLoader(ds, batch_size=16, shuffle=True, collate_fn=collate_fn)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = StrokeLSTM().to(device)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)

    for epoch in range(1, 41):
        loss = train_epoch(model, opt, dl, device)
        print(f"Epoch {epoch} loss {loss:.6f}")
        if epoch % 10 == 0:
            save_model(model, f"stroke_lstm_epoch{epoch}.pth")

if __name__ == "__main__":
    main()
