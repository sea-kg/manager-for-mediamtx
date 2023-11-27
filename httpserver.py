#!/usr/bin/env python3

import os
import subprocess
import json
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer



def get_list_ffmpegs():
    result = subprocess.run(['ps', '-aux'], stdout=subprocess.PIPE)
    result = result.stdout.decode("utf-8")
    result = result.split("\n")
    ret = {
        'count': 0,
        'list': [],
    }
    for _line in result:
        if 'ffmpeg' in _line:
            _cmd = _line.split(" ")
            _cmd = list(filter(None, _cmd))
            _cmd_ffmpeg = _cmd[_cmd.index("ffmpeg"):]
            stream_info = {
                "original": _line,
                # "cmd": _cmd,
                "command": " ".join(_cmd_ffmpeg),
                "pid": _cmd[1],
                "cpu": _cmd[2] + "%",
                "memory": _cmd[3] + "%",
            }
            ret['list'].append(stream_info)
    ret['count'] = len(ret['list'])
    # TODO https://bluenviron.github.io/mediamtx/#operation/configPathsList
    return ret

def get_list_video_files():
    _script_dir = os.path.dirname(os.path.realpath(__file__))
    _script_dir = os.path.abspath(_script_dir)
    _video_files = os.path.join(_script_dir, "video-files")
    ret = {
        'count': 0,
        'list': [],
    }
    _files = os.listdir(_video_files)
    for _filepath in _files:
        _fullpath = os.path.join(_video_files, _filepath)
        if os.path.isfile(_fullpath):
            file_stats = os.stat(_fullpath)
            _file_info = {
                "size_in_bytes": file_stats.st_size,
                "name": _filepath,
                "ffprobe": {},
            }
            result = subprocess.run(['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', '-print_format', 'json', _fullpath], stdout=subprocess.PIPE)
            result = result.stdout.decode("utf-8")
            _file_info["ffprobe"] = json.loads(result)
            ret['list'].append(_file_info)
    ret['count'] = len(ret['list'])
    return ret

class HttpGetHandler(BaseHTTPRequestHandler):
    """
        handler for get requests
        https://docs-python.ru/standart-library/modul-http-server-python/klass-basehttprequesthandler/
    """

    def do_GET(self):
        _script_dir = os.path.dirname(os.path.realpath(__file__))
        _script_dir = os.path.abspath(_script_dir)
        _html_dir = os.path.join(_script_dir, "html")

        _path = ""
        if '?' in self.path:
            _path = self.path.split("?")[0]
        else:
            _path = self.path
        if _path == "/":
            _path = "/index.html"
        _path = os.path.normpath(_path)
        _filepath = os.path.join(_html_dir, _path[1:])
        if os.path.isfile(_filepath):
            # print(self.path, " -> ", _filepath)
            self.send_response(200)
            # https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types
            if _filepath.lower().endswith("html"):
                self.send_header("Content-type", "text/html")
            elif _filepath.lower().endswith("js"):
                self.send_header("Content-type", "application/javascript")
            elif _filepath.lower().endswith("png"):
                self.send_header("Content-type", "image/png")
            elif _filepath.lower().endswith("css"):
                self.send_header("Content-type", "text/css")
            else:
                self.send_header("Content-type", "application/octet-stream")
            self.end_headers()
            with open(_filepath, "rb") as _file:
                _content = _file.read()
                self.wfile.write(_content)
        elif _path == "/api/list-running-streams":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(get_list_ffmpegs()).encode("utf-8"))
        elif _path == "/api/mediamtx_log":
            self.send_response(200)
            self.send_header("Content-type", "text/plain;charset=UTF-8")
            self.end_headers()
            _mediamtx_log = os.path.join(_script_dir, "mediamtx", "mediamtx.log")
            with open(_mediamtx_log, "rb") as _file:
                _content = _file.read()
                self.wfile.write(_content)
        elif _path == "/api/video-files":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(get_list_video_files()).encode("utf-8"))
        else:
            self.send_response(404)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write('<html><head><meta charset="utf-8">'.encode())
            self.wfile.write('<title>HTTP 404 - Not found.</title></head>'.encode())
            self.wfile.write('<body>HTTP 404 - Not found</body></html>'.encode())


def run(server_class=HTTPServer, handler_class=HttpGetHandler):
    print("\nHello! This is manager for test streams to mediamtx server\n\n")

    _script_dir = os.path.dirname(os.path.realpath(__file__))
    _script_dir = os.path.abspath(_script_dir)
    os.chdir(_script_dir)
    print("Current work directory " + os.getcwd())

    port = 8083
    print("Listening web server " + str(port) + " ... \n")
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()

run()