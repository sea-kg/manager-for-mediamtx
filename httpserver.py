#!/usr/bin/env python3

import os
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer






class HttpGetHandler(BaseHTTPRequestHandler):
    """
        handler for get requests
        https://docs-python.ru/standart-library/modul-http-server-python/klass-basehttprequesthandler/
    """

    def do_GET(self):
        _html_dir = os.path.dirname(os.path.realpath(__file__))
        _html_dir = os.path.abspath(_html_dir)
        _html_dir = os.path.join(_html_dir, "html")

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
            print(self.path, " -> ", _filepath)
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            with open(_filepath, "r") as _file:
                _content = _file.read()
                self.wfile.write(_content.encode("utf-8"))
        else:
            self.send_response(404)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write('<html><head><meta charset="utf-8">'.encode())
            self.wfile.write('<title>Простой HTTP-сервер.</title></head>'.encode())
            self.wfile.write('<body>Был получен GET-запрос.</body></html>'.encode())


def run(server_class=HTTPServer, handler_class=HttpGetHandler):
    print("Listening 8083 ... ")
    server_address = ('', 8083)
    httpd = server_class(server_address, handler_class)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()

run()