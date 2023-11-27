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