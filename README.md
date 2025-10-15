<div align="center">
  <h1>Account and time-manager for social networks</h1> 
</div>

I made this bot for my own purposes, so it's not really adapted to run on other people's servers. But since I don't have much memory, I personally use systemmd for this purpose with a prepared directory in which I just update the scripts and restart the process. Yes, in the old days,

### 🏗️ How to rebuild (only for me)

1. Prepare the directory and clone the repo 

```
cd /opt/toples-bot
git clone --depth 1 https://github.com/subpolare/account-manager
mv account-manager/* ./
rm -r account-manager/*
```

2. Create virtualenv and install dependencies

```
python3 -m venv .venv
./.venv/bin/python -m pip install -U pip wheel
./.venv/bin/pip install -r requirements.txt
```

3. Enable and start the service, follow logs

```
sudo systemctl restart toples-bot
sudo journalctl -u toples-bot -n 100 -o cat
```
