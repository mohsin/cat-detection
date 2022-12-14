# Cat Detection #

### Introduction ###
I recently started facing an issue--a wild cat was pooping outside my apartment on my doormat. I figured it would be a good time to put the Raspberry Pi to use to scare the cat away.

## Setup ##
First install all the dependencies using:
```zsh
pip install -r requirements.txt
```
As you see in requirements, the AWS CLI is installed so you would need to link the AWS API credentials to the AWS console. Once complete, you can run the program.

I have added a setup mode for convience so you can setup and align the camera to the field of view properly before running it properly. You can enter setup mode using:

```zsh
python main.py --setup
```
**Click to see introduction on youtube:**

[![Demonstration of the project setup mode](https://img.youtube.com/vi/Ii_dgGC3IoM/0.jpg)](https://www.youtube.com/watch?v=Ii_dgGC3IoM)


### Solution ###
This code makes a dog barking sound whenever a cat comes into the view of the pi camera, thus scaring the cat away.

**Click to see demonstration on youtube:**

[![Demonstration of the project](https://img.youtube.com/vi/4e4OTL9MR1c/0.jpg)](https://www.youtube.com/watch?v=4e4OTL9MR1c)

### Requirements ###
* Raspberry Pi Zero W (although it should work on others too).
* A [Pi Camera module](https://robu.in/product/5mp-raspberry-pi-camera-module-w-hbv-ffc-cable)
* Programming skill to set this up.
* There should be a file `apicount.txt` where the main.py is with a single number 0 as it's contents.

### Running ###
1. Setup Raspberry Pi with camera (legacy mode enabled until picamera2 is stable).
2. Pull the required libraries boto3, pycamera, etc. using pip install (will all requirements.txt to this repo later).
3. Setup AWS console with it's keys so that boto3 can access them while running script.
4. Ensure that aplay works fine while running dog.wav using bluealsa.

I usually SSH into my Pi to run modules, so the script dies if I SSH out as the terminal no longer exists. So instead of running `python main.py` (for development), I run the script like this in production:
```zsh
python /home/mohsin/cat-detector/main.py < /dev/null > output.txt 2>&1 &
```
In order to terminate the process when run like this, `pkill python` or `ps aux | grep python`, then `kill <id-of-process>`.

Alternatively, install [supervisor](http://supervisord.org) using:
```zsh
sudo apt-get install supervisor
```
And then add this `cat-detector-worker.conf` configuration inside `/etc/supervisor/conf.d` to run ensure that it runs when the Pi starts and runs continously...
```zsh
[program:cat-detector]
process_name=%(program_name)s_%(process_num)02d
command=python /home/mohsin/cat-detector/main.py
autostart=true
autorestart=true
user=mohsin
numprocs=1
redirect_stderr=true
stderr_logfile=/home/mohsin/cat-detector/err.log
stdout_logfile=/home/mohsin/cat-detector/out.log
```

And that's it. You can now run the program normally, and find the output motion captures inside the *captures* folder. I also have included a one liner below which I use to convert all the .h246 files in captures to .mp4 using `ffmpeg` for convenience.
```zsh
for file in *.h264; do ffmpeg -i $file out-$file.mp4; done
```

### Limitations ###
* I'm using system call to aplay to stream the sound using my wireless bluetooth speaker. Ideally, I'd prefer it done natively but I had issues setting up bluealsa and pulseaudio to run as daemons so eventually gave up. This causes a delay, in addition to some other delays in the project.
* This uses Amazon Rekognition to detect the cat than an in-built trained model so WiFi and an Amazon account is needed. (I used their free tier offering so I'm counting the API calls on this project).
