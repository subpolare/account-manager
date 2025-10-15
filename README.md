<div align="center">
  <h1>Account and time-manager for social networks</h1> 
</div>

### 🏗️ How to build

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
