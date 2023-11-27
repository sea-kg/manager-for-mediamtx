# manager-for-mediamtx

* Used [mediamtx 1.3.1](https://github.com/bluenviron/mediamtx)


## Run


```
$ cd mediamtx
$ docker-compose up
```


## Start from desktop (linux + ffmpeg)

Start stream from desktop:

```
$ ffmpeg -video_size 256x256 -framerate 25 -f x11grab -i $DISPLAY.0+75,150 -strict -2 -c:v libvpx-vp9 -an -f rtsp -rtsp_transport tcp rtsp://localhost:8554/desktop1
```

## Transcoding

From mp4 to vp9 via ffmpeg

```
$ ffmpeg -i video-files/channel_001.mp4 -c:v libvpx-vp9 -crf 30 -b:v 64k -bufsize 64k -an video-files/channel_001.webm
```


## ffplay

```
$ ffplay -fflags nobuffer rtsp://localhost:8554/desktop1
```