function human_file_size(bytes, si=false, dp=1) {
    const thresh = si ? 1000 : 1024;
    if (Math.abs(bytes) < thresh) {
      return bytes + ' B';
    }
    const units = si
      ? ['kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
      : ['KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'];
    let u = -1;
    const r = 10**dp;
    do {
      bytes /= thresh;
      ++u;
    } while (Math.round(Math.abs(bytes) * r) / r >= thresh && u < units.length - 1);
    return bytes.toFixed(dp) + ' ' + units[u];
}

function update_list_of_streams() {
    $.ajax({
        url: '/api/list-running-streams',
        method: 'get',
        dataType: 'json',
    }).done(function(data) {
        var another_streams_html = '';
        var need_update_list_of_files = false;
        for (var i in data.list) {
            var _stream_info = data.list[i];
            var elm_id = 'video_file_' + _stream_info.filename + '_cmd_block';
            var elm = document.getElementById(elm_id)
            if (elm === undefined && _stream_info.filename != "") {
                need_update_list_of_files = true;
            }
            if (elm) {
                elm.style.display = "";
                document.getElementById('video_file_' + _stream_info.filename + '_command').innerHTML = _stream_info.command;
                document.getElementById('video_file_' + _stream_info.filename + '_info').innerHTML = 'CPU: ' + _stream_info.cpu + ' | Memory: ' + _stream_info.memory;
                document.getElementById('video_file_' + _stream_info.filename + '_kill').style.display = '';
                document.getElementById('video_file_' + _stream_info.filename + '_kill').setAttribute("pid", _stream_info.pid);
                document.getElementById('video_file_' + _stream_info.filename + '_kill').innerHTML = 'kill -9 ' + _stream_info.pid;
            } else {
                another_streams_html += '<div class="video-file-command-stream">'
                another_streams_html += '<div class="command">' + _stream_info.command + '</div>'
                another_streams_html += '<div class="info">CPU: ' + _stream_info.cpu + ' | Memory: ' + _stream_info.memory + '</div>'
                another_streams_html += '</div>'
            }
        }
        document.getElementById('another_streams').innerHTML = another_streams_html;
        // console.log(data)
        if (need_update_list_of_files) {
            update_video_files();
        }
    }).fail(function(err) {
        console.error(err) // TODO show error
    })
}

function start_stream(filename, protocol) {
    $.ajax({
        url: '/api/start-stream',
        method: 'get',
        dataType: 'json',
        data: {
            'filename': filename,
            'protocol': protocol,
        },
    }).done(function(data) {
        console.log(data)
        update_list_of_streams();
    }).fail(function(err) {
        console.error(err) // TODO show error
    })
}

function kill_stream(el) {
    $.ajax({
        url: '/api/kill-stream',
        method: 'get',
        dataType: 'json',
        data: {
            'pid': $(el).attr('pid'),
        },
    }).done(function(data) {
        console.log("kill_stream", data)
    }).fail(function(err) {
        console.error("kill_stream", err) // TODO show error
    })
}

var progress_bar_file_size = 0;
var progress_bar_uploaded_chanks = 0;

var upload_chanks = []

function update_progress_bar() {
    document.getElementById("progress_bar_value").style.width = Math.round((progress_bar_uploaded_chanks * 100) / progress_bar_file_size) + "%";
}

function start_upload_chanks_to_server() {
    // console.log(upload_chanks)
    var upload_next_chank = upload_chanks.pop();
    if (upload_next_chank === undefined) return;
    $.ajax({
        url: '/api/upload-file?cmd=chank&fileid=' + upload_next_chank["fileid"] + "&pos=" + upload_next_chank["pos"] + "&data_len=" + upload_next_chank["data_len"],
        method: 'post',
        // dataType: 'application/octet-stream',
        data: upload_next_chank.data,
    }).fail(function(err) {
        console.error("upload_file_to_server (chank)", err) // TODO show error
    }).done(function(recive_data) {
        // console.log(recive_data)
        progress_bar_uploaded_chanks += upload_next_chank.data_len;
        update_progress_bar();
        setTimeout(start_upload_chanks_to_server, 1);
    })
}

function upload_file_to_server(file_info, arr_buffer) {
    var binary = '';
    progress_bar_file_size = file_info.size;
    progress_bar_uploaded_chanks = 0;
    update_progress_bar();
    $.ajax({
        url: '/api/upload-file',
        method: 'get',
        dataType: 'json',
        data: {
            'cmd': 'init',
            'filesize': file_info.size,
            'filename': file_info.name,
            'filetype': file_info.type,
        },
    }).fail(function(err) {
        console.error("upload_file_to_server (init)", err) // TODO show error
    }).done(function(data) {
        console.log("upload_file_to_server (init)", data)
        var bytes = new Uint8Array(arr_buffer);
        var len = bytes.byteLength;
        var pos = 0;
        var chank_size = Math.round(len / 100);
        upload_chanks = []
        for (var i = 0; i < len; i++) {
            binary += String.fromCharCode( bytes[ i ] );
            if (binary.length >= chank_size) {
                upload_chanks.push({
                    'cmd': 'chank',
                    'fileid': data["fileid"],
                    'pos': pos,
                    'data_len': binary.length,
                    'data': binary,
                })
                binary = ""
                pos = i;
                // break;
            }
        }
        if (binary.length > 0) {
            upload_chanks.push({
                'cmd': 'chank',
                'fileid': data["fileid"],
                'pos': pos,
                'data_len': binary.length,
                'data': binary,
            })
        }
        console.log("Prepared chnaks to upload")
        start_upload_chanks_to_server();
    })
}

function upload_file(el) {
    var file_to_upload_element = document.getElementById("file_to_upload");
    let file_info = file_to_upload_element.files[0]

    let reader = new FileReader();
    reader.onload = (function(theFile) {
        return function(e) {
            upload_file_to_server(theFile, e.target.result)
        };
    })(file_info);
    // reader.readAsText(file_info);
    reader.readAsArrayBuffer(file_info);
}

function update_video_files() {
    $.ajax({
        url: '/api/video-files',
        method: 'get',
        dataType: 'json',
        // data: {text: 'Текст'},     /* Параметры передаваемые в запросе. */
    }).done(function(data) {
        var elem = document.getElementById('list_of_files');
        for (var i in data.list) {
            var file_info = data.list[i];
            console.log(file_info);
            var new_elem_id = "video_file_" + file_info.name;
            if (document.getElementById(new_elem_id) === null) {
                _html = '';
                _html += '<div class="video-file-info" id="' + new_elem_id + '">';
                _html += '<div class="video-file-title">' + file_info.name + ' (' + human_file_size(file_info.size_in_bytes) + ')</div>';
                _html += '<div class="video-file-command-stream" id="video_file_' + file_info.name + '_cmd_block" style="display: none">'
                _html += '   <div class="command" id="video_file_' + file_info.name + '_command"></div>'
                _html += '   <div class="info" id="video_file_' + file_info.name + '_info"></div>'
                _html += '</div>';
                _html += '<div class="video-file-btn" id="video_file_' + file_info.name + '_kill" pid="-1" onclick="kill_stream(this);" style="display: none">kill</div>';
                _html += '<div class="video-file-btn" onclick="start_stream(\'' + file_info.name + '\', \'tcp\');">start (tcp)</div>';
                _html += '<div class="video-file-btn" onclick="start_stream(\'' + file_info.name + '\', \'udp\');">start (udp)</div>';
                _html += '</div>';
                elem.innerHTML += _html;
            }
        }
        update_list_of_streams();
    });
}

document.addEventListener("DOMContentLoaded", function(event) {
    update_video_files();
    setInterval(update_list_of_streams, 3000);
});