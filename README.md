# Cat Detection #

> :warning: This is currently a work in progress so everything below are merely "claims" to what the final product should work as. Once completed, I'll remove this line.

### Introduction ###
I recently started facing an issue--a wild cat was pooping outside my apartment on my doormat. I figured it would be a good time to put the Raspberry Pi to use to scare the cat away.

### Solution ###
This code makes a dog barking sound whenever a cat comes into the view of the pi camera, this scaring the dog away.

### Requirements ###
* Raspberry Pi Zero W (although it should work on others too).
* A [Pi Camera module](https://robu.in/product/5mp-raspberry-pi-camera-module-w-hbv-ffc-cable)
* Programming skill to set this up.

### Limitations ###
* I'm using system call to aplay to stream the sound using my wireless bluetooth speaker. Ideally, I'd prefer it done natively but I had issues setting up bluealsa and pulseaudio to run as daemons so eventually gave up.
* This uses Amazon Rekognition to detect the cat than an in-built trained model so WiFi and an Amazon account is needed. (I used their free tier offering so I'm counting the API calls on this project).

