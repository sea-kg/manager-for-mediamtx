#!/usr/bin/env python3

import os
import subprocess
import json
import hashlib
import base64
import urllib
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
            _filename = ""
            if "video-files/" in _line:
                _filename = _line.split("video-files/")[1].split(" ")[0]
            stream_info = {
                "original": _line,
                "filename": _filename,
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
        if _fullpath.endswith('.txt'):
            continue
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

def send_error(handler, code, message):
    handler.send_response(code)
    handler.send_header("Content-type", "application/json")
    handler.end_headers()
    response = {"error": message}
    handler.wfile.write(json.dumps(response).encode("utf-8"))

class HttpGetHandler(BaseHTTPRequestHandler):
    """
        handler for get requests
        https://docs-python.ru/standart-library/modul-http-server-python/klass-basehttprequesthandler/
    """

    def do_GET(self):
        _script_dir = os.path.dirname(os.path.realpath(__file__))
        _script_dir = os.path.abspath(_script_dir)
        _html_dir = os.path.join(_script_dir, "html")
        _upload_dir = os.path.join(_script_dir, "upload-files")

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
        elif _path == "/api/upload-file":
            params = self.path[self.path.index("?")+1:]
            params = urllib.parse.parse_qs(params)
            print(params)
            if "cmd" not in params:
                send_error(self, 400, "Expected input param cmd")
                return

            cmd = params["cmd"][0]
            if cmd != "init" and cmd != "chank":
                send_error(self, 400, "Expected input param cmd init or chank")
                return
            if cmd == "init":
                fmeta = {
                    "fileid": "",
                    "filename": params["filename"][0],
                    "filesize": int(params["filesize"][0]),
                    "filetype": params["filetype"][0],
                    "chanks": [],
                }
                if fmeta["filename"] is None:
                    send_error(self, 400, "Expected input param filename")
                    return
                if fmeta["filesize"] is None:
                    send_error(self, 400, "Expected input param filesize")
                    return
                if fmeta["filetype"] is None:
                    send_error(self, 400, "Expected input param filetype")
                    return
                fmeta["fileid"] = hashlib.md5(fmeta["filename"].encode()).hexdigest()
                fmeta_filepath = os.path.join(_upload_dir, fmeta["fileid"] + ".json")
                if os.path.isfile(fmeta_filepath):
                    os.remove(fmeta_filepath)
                with open(fmeta_filepath, "wb") as _file:
                    _file.write(json.dumps(fmeta, indent=4).encode("utf-8"))
                target_file = os.path.join(_upload_dir, fmeta["fileid"] + ".data")
                if os.path.isfile(target_file):
                    os.remove(target_file)
                with open(target_file, "wb") as _file:
                    _file.seek(fmeta["filesize"]-1)
                    _file.write(b"\0")
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(fmeta).encode("utf-8"))
                return
            send_error(self, 500, "what?")

        elif _path == "/api/start-stream":
            i = self.path.index ( "?" ) + 1
            params = dict ( [ tuple ( p.split("=") ) for p in self.path[i:].split ( "&" ) ] )
            _filename = params["filename"]
            _protocol = params["protocol"]
            _cmd = ""
            _cmd += "ffmpeg -re -stream_loop -1 -i "
            _cmd += " video-files/" + _filename + " "
            _cmd += " -strict -2 " # need for vp9 experimental
            _cmd += " -c:v copy -an -f rtsp -rtsp_transport " + _protocol + "  "
            _cmd += " rtsp://localhost:8554/" + _filename
            _cmd += " > video-files/" + _filename + ".txt 2>&1 &"
            ret_code = os.system(_cmd)
            ret = {
                "exit_code": ret_code,
                "command": _cmd,
            }
            if ret_code == 0:
                self.send_response(200)
            else:
                self.send_response(400)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(ret).encode("utf-8"))
        else:
            self.send_response(404)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write('<html><head><meta charset="utf-8">'.encode())
            self.wfile.write('<title>HTTP 404 - Not found.</title></head>'.encode())
            self.wfile.write('<body>HTTP 404 - Not found</body></html>'.encode())

    def do_POST(self):
        _script_dir = os.path.dirname(os.path.realpath(__file__))
        _script_dir = os.path.abspath(_script_dir)
        _html_dir = os.path.join(_script_dir, "html")
        _upload_dir = os.path.join(_script_dir, "upload-files")

        _path = ""
        if '?' in self.path:
            _path = self.path.split("?")[0]
        if _path == "/api/upload-file":
            params = self.path[self.path.index("?")+1:]
            params = urllib.parse.parse_qs(params)
            # print(params)
            if "cmd" not in params:
                send_error(self, 400, "Expected input param cmd")
                return

            cmd = params["cmd"][0]
            if cmd != "init" and cmd != "chank":
                send_error(self, 400, "Expected input param cmd init or chank")
                return
            if cmd == "chank":
                fileid = params["fileid"][0]
                pos = int(params["pos"][0])
                data_len = int(params["data_len"][0])
                target_file = os.path.join(_upload_dir, fileid + ".data")
                if not os.path.isfile(target_file):
                    send_error(self, 404, "Not found fileid=" + fileid)
                    return
                fmeta_filepath = os.path.join(_upload_dir, fileid + ".json")
                if not os.path.isfile(fmeta_filepath):
                    send_error(self, 404, "Not found fmeta_filepath = " + fmeta_filepath)
                    return
                content_len = int(self.headers['content-length'])
                print(content_len)
                print(data_len)
                post_body = self.rfile.read(data_len)
                print(len(post_body))
                with open(target_file, "r+b") as _file:
                    _file.seek(pos, 0)
                    _file.write(post_body)
                    with open(fmeta_filepath, "rt") as _file:
                        fmeta = json.load(_file)
                    fmeta["chanks"].append({
                        "pos": pos,
                        "len": len(post_body),
                    })
                    with open(fmeta_filepath, "wb") as _file:
                        _file.write(json.dumps(fmeta, indent=4).encode("utf-8"))
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(fmeta).encode("utf-8"))
                return
            send_error(self, 500, "what?")


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