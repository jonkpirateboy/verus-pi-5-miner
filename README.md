# Verus Mining Appliance for Raspberry Pi

**A fully automated, headless Verus miner with a real-time TFT dashboard**

This guide shows how to turn a Raspberry Pi 5 (or Pi 4) into a standalone, plug-and-play Verus mining appliance featuring:

* Verus CPU mining via ccminer
* Automatic startup on boot (miner + dashboard)
* Real-time **hacker-style dashboard** on a 480×320 SPI TFT (ILI9486)
* ANSI-cleaned miner logs, share tracking, MH/s display, uptime, shares/min
* Writes directly to `/dev/fb0` (no desktop required)
* Global kernel cursor disable (no blinking “_” on screen)
* Fully controlled via systemd

This README documents the entire setup end-to-end.

## Hardware Requirements

* **Raspberry Pi 5** (recommended) or Pi 4
* **480×320 SPI TFT** using ILI9486 / fb_ili9486 framebuffer
* Raspberry Pi OS **Lite (Trixie)**
* Stable internet connection
* 5V/5A power (Pi 5 recommended)

## Install

### 1. Install Required Packages

```bash
sudo apt update
sudo apt install -y git python3 python3-pip python3-pil python3-numpy libcurl4-openssl-dev libssl-dev libjansson-dev automake autotools-dev build-essential fonts-dejavu-core fonts-dejavu-extra
```

Add your user to the `video` group so Python can write to `/dev/fb0`:

```bash
sudo usermod -aG video jonk
```

Reboot after this:

```bash
sudo reboot
```

### 2. LCD screen
To install support for the LCD screen, enter the following commands:

```
git clone https://github.com/goodtft/LCD-show.git
cd LCD-show
sudo ./LCD35-show
```

This reboots the machine automatically and should show the terminal login on the LCD screen. 

If the screen is upside down enter this command: `sudo nano /boot/config.txt` and under `[all]`, change `dtoverlay=tft35a:rotate=90` to `dtoverlay=tft35a:rotate=270` and save. Then enter: `sudo reboot`

### 3. Install Verus-optimized ccminer

```bash
cd ~
git clone --single-branch -b ARM https://github.com/monkins1010/ccminer.git
cd ccminer
chmod +x autogen.sh configure.sh build.sh
./autogen.sh
CC=gcc CXX=g++ ./build.sh
./ccminer --help
```

This produces a `ccminer` binary optimized for ARM CPUs (Raspberry Pi).

### 4. Start Mining (Manual Test)

Replace the wallet address with your own:

```bash
cd ~/ccminer
./ccminer -a verus \
  -o stratum+tcp://sg.vipor.net:5040 \
  -u RP5uqbvzmCg7FtFS6WcKPHuAq7HihEkHmY.Pi5 \
  -p x \
  -t 4 \
  2>&1 | tee /tmp/verus_raw.log
```

This writes live miner output to:

```
/tmp/verus_raw.log
```

The dashboard uses this file.

### 5. Create the TFT Dashboard

git clone https://github.com/jonkpirateboy/verus-pi-5-miner.git

Make it executable:

```bash
chmod +x ~/verus-pi-5-miner/verus_lcd_dashboard.py
```

Test it manually:

```bash
python3 ~/verus-pi-5-miner/verus_lcd_dashboard.py
```

If your screen lights up, perfect. It will not be mining yet though.

### 6. Disable the Blinking Cursor (Kernel-Level)

Edit the kernel cmdline:

```bash
sudo nano /boot/firmware/cmdline.txt
```

Append at the end of the single line (with a space before):

```
 vt.global_cursor_default=0
```

Save + reboot:

```bash
sudo reboot
```

Cursor will now *never* appear, even before services run.

### 7. Create Miner Autostart Service

```bash
sudo cp -av ~/verus-pi-5-miner/verus-miner.service /etc/systemd/system/
```

Enable:

```bash
sudo systemctl daemon-reload
sudo systemctl enable verus-miner.service
sudo systemctl start verus-miner.service
```

### 8. Create Dashboard Autostart Service

```bash
sudo cp -av ~/verus-pi-5-miner/verus-dashboard.service /etc/systemd/system/
```

Enable:

```bash
sudo systemctl daemon-reload
sudo systemctl enable verus-dashboard.service
sudo systemctl start verus-dashboard.service
```

### 9. Full Boot Test

Reboot:

```bash
sudo reboot
```

Expected results:

* ccminer starts automatically
* `/tmp/verus_raw.log` is created
* TFT lights up with the dashboard
* No blinking cursor
* Logs scroll live
* Hashrate, shares, uptime, shares/min visible

Your Raspberry Pi is now a **self-contained Verus mining appliance**.

# Final Result

You now have:

* A fully automated Verus mining rig
* Real-time TFT dashboard
* No desktop environment required
* No cursor, no clutter
* Plug-and-play appliance behavior

Enjoy your custom mining machine!
